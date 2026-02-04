"""
ReconX Authentication Service
Handles JWT authentication, MFA, password management, and user sessions
"""

import jwt
import pyotp
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Union
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app, request

from config import config
from utils.logger import security_logger, get_logger
from utils.security import validate_password, validate_email, validate_username
from database import user_manager, audit_manager

logger = get_logger('auth_service')

class AuthenticationService:
    """Main authentication service for ReconX"""
    
    def __init__(self):
        self.jwt_secret = config.JWT_SECRET_KEY
        self.access_token_expires = config.JWT_ACCESS_TOKEN_EXPIRES
        self.refresh_token_expires = config.JWT_REFRESH_TOKEN_EXPIRES
    
    def authenticate_user(self, username: str, password: str, ip_address: str) -> Tuple[bool, Dict, str]:
        """
        Authenticate user with username and password
        
        Returns:
            Tuple[bool, Dict, str]: (success, user_data, error_message)
        """
        try:
            # Get user from database
            user = user_manager.get_user_by_username(username)
            if not user:
                security_logger.log_failed_login(username, ip_address, "User not found")
                return False, {}, "Invalid username or password"
            
            # Check if account is locked
            if user.get('status') == 'locked':
                if user.get('account_locked_until'):
                    lockout_time = user['account_locked_until']
                    if datetime.now() < lockout_time:
                        remaining_time = int((lockout_time - datetime.now()).total_seconds())
                        security_logger.log_failed_login(username, ip_address, "Account locked")
                        return False, {}, f"Account is locked. Try again in {remaining_time} seconds"
                    else:
                        # Unlock account
                        user_manager.update_user_status(user['user_id'], 'active')
                        user_manager.reset_failed_login_attempts(user['user_id'])
            
            # Check if account is inactive
            if user.get('status') != 'active':
                security_logger.log_failed_login(username, ip_address, f"Account status: {user.get('status')}")
                return False, {}, "Account is not active"
            
            # Verify password
            if not check_password_hash(user['password_hash'], password):
                # Increment failed login attempts
                failed_attempts = user.get('failed_login_attempts', 0) + 1
                user_manager.update_failed_login_attempts(user['user_id'], failed_attempts)
                
                # Check if account should be locked
                if failed_attempts >= config.LOGIN_MAX_ATTEMPTS:
                    lockout_until = datetime.now() + timedelta(minutes=config.LOGIN_LOCKOUT_DURATION)
                    user_manager.lock_account(user['user_id'], lockout_until)
                    security_logger.log_failed_login(username, ip_address, "Account locked due to too many failed attempts")
                    return False, {}, f"Too many failed attempts. Account locked for {config.LOGIN_LOCKOUT_DURATION} minutes"
                
                security_logger.log_failed_login(username, ip_address, "Invalid password")
                remaining_attempts = config.LOGIN_MAX_ATTEMPTS - failed_attempts
                return False, {}, f"Invalid password. {remaining_attempts} attempts remaining"
            
            # Reset failed login attempts on successful login
            user_manager.reset_failed_login_attempts(user['user_id'])
            
            # Update last login
            user_manager.update_last_login(user['user_id'])
            
            # Log successful login
            security_logger.log_login_attempt(username, True, ip_address, user_id=user['user_id'])
            
            # Check if MFA is required
            if user.get('mfa_required') and not user.get('mfa_enabled'):
                return True, user, "MFA setup required"
            
            return True, user, ""
            
        except Exception as e:
            logger.error(f"Authentication error for user {username}: {e}")
            return False, {}, "Authentication service error"
    
    def generate_tokens(self, user: Dict) -> Dict[str, str]:
        """Generate JWT access and refresh tokens"""
        try:
            now = datetime.utcnow()
            
            # Access token payload
            access_payload = {
                'user_id': user['user_id'],
                'username': user['username'],
                'role_id': user['role_id'],
                'role_name': user.get('role_name', ''),
                'mfa_enabled': user.get('mfa_enabled', False),
                'mfa_required': user.get('mfa_required', False),
                'exp': now + timedelta(hours=self.access_token_expires),
                'iat': now,
                'type': 'access'
            }
            
            # Refresh token payload
            refresh_payload = {
                'user_id': user['user_id'],
                'username': user['username'],
                'exp': now + timedelta(days=self.refresh_token_expires),
                'iat': now,
                'type': 'refresh'
            }
            
            # Generate tokens
            access_token = jwt.encode(access_payload, self.jwt_secret, algorithm='HS256')
            refresh_token = jwt.encode(refresh_payload, self.jwt_secret, algorithm='HS256')
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': self.access_token_expires * 3600,  # seconds
                'refresh_expires_in': self.refresh_token_expires * 86400  # seconds
            }
            
        except Exception as e:
            logger.error(f"Token generation error: {e}")
            raise
    
    def verify_token(self, token: str, token_type: str = 'access') -> Tuple[bool, Dict, str]:
        """
        Verify JWT token and return user data
        
        Returns:
            Tuple[bool, Dict, str]: (valid, payload, error_message)
        """
        try:
            # Decode token
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            # Check token type
            if payload.get('type') != token_type:
                return False, {}, "Invalid token type"
            
            # Check expiration
            if datetime.utcnow().timestamp() > payload['exp']:
                return False, {}, "Token expired"
            
            # Get fresh user data
            user = user_manager.get_user_by_id(payload['user_id'])
            if not user or user.get('status') != 'active':
                return False, {}, "User not found or inactive"
            
            # Update payload with fresh user data
            payload.update({
                'role_name': user.get('role_name', ''),
                'mfa_enabled': user.get('mfa_enabled', False),
                'mfa_required': user.get('mfa_required', False)
            })
            
            return True, payload, ""
            
        except jwt.ExpiredSignatureError:
            return False, {}, "Token expired"
        except jwt.InvalidTokenError as e:
            return False, {}, f"Invalid token: {str(e)}"
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return False, {}, "Token verification error"
    
    def refresh_access_token(self, refresh_token: str) -> Tuple[bool, Dict, str]:
        """Generate new access token using refresh token"""
        try:
            # Verify refresh token
            valid, payload, error = self.verify_token(refresh_token, 'refresh')
            if not valid:
                return False, {}, error
            
            # Get fresh user data
            user = user_manager.get_user_by_id(payload['user_id'])
            if not user:
                return False, {}, "User not found"
            
            # Generate new access token
            tokens = self.generate_tokens(user)
            
            return True, tokens, ""
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False, {}, "Token refresh error"
    
    def create_user_session(self, user_id: int, token_hash: str, ip_address: str) -> str:
        """Create user session and return session ID"""
        try:
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=self.access_token_expires)
            
            # Store session in database
            user_manager.create_user_session(
                session_id=session_id,
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=request.headers.get('User-Agent', '')
            )
            
            return session_id
            
        except Exception as e:
            logger.error(f"Session creation error: {e}")
            raise
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate user session"""
        try:
            return user_manager.invalidate_session(session_id)
        except Exception as e:
            logger.error(f"Session invalidation error: {e}")
            return False
    
    def invalidate_all_user_sessions(self, user_id: int) -> bool:
        """Invalidate all sessions for a user"""
        try:
            return user_manager.invalidate_all_user_sessions(user_id)
        except Exception as e:
            logger.error(f"User session invalidation error: {e}")
            return False

class MFAService:
    """Multi-Factor Authentication service"""
    
    def __init__(self):
        self.issuer = config.MFA_ISSUER
        self.algorithm = config.MFA_ALGORITHM
        self.digits = config.MFA_DIGITS
        self.period = config.MFA_PERIOD
    
    def generate_mfa_secret(self, user_id: int, username: str) -> Dict[str, str]:
        """Generate MFA secret and QR code data"""
        try:
            # Generate secret key
            secret = pyotp.random_base32()
            
            # Generate backup codes
            backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]
            
            # Store MFA secret
            user_manager.create_mfa_secret(user_id, secret, backup_codes)
            
            # Generate QR code URI
            totp = pyotp.TOTP(secret, digits=self.digits, interval=self.period)
            provisioning_uri = totp.provisioning_uri(
                name=username,
                issuer_name=self.issuer
            )
            
            return {
                'secret': secret,
                'backup_codes': backup_codes,
                'qr_code_uri': provisioning_uri
            }
            
        except Exception as e:
            logger.error(f"MFA secret generation error: {e}")
            raise
    
    def verify_mfa_code(self, user_id: int, code: str) -> Tuple[bool, str]:
        """Verify MFA TOTP code"""
        try:
            # Get user's MFA secret
            mfa_secret = user_manager.get_mfa_secret(user_id)
            if not mfa_secret:
                return False, "MFA not configured"
            
            # Check if it's a backup code
            if code in mfa_secret.get('backup_codes', []):
                # Use backup code (remove it after use)
                user_manager.use_backup_code(user_id, code)
                return True, ""
'5ö¡q±'Æ‘,`ıali«æ³Z›â’¸Ì’…M¬                       8  $şA›t4¶‘0)‘VÿÉ÷ÛwÑ¾¢ôUX¨ëÓŠÃ}JöƒÚE¢²øQ6×NÑ}J?+ZßºdLÃjáfp5Ô¼d˜Ìlêño\Õ©Å}Kš7M­ì<Õ…çÁ#=ájüìd4J):shÙƒà6çª=Ö¯ ±ğEÄ~>*Lrqé±™•®ô§øcH¦ƒ68:¯P Oê6}ÍÇƒs\÷>o8ÕîŒ¬£fÎtLß…\´°ø?«áÀì:&D$<âà½I8ù¹˜PcÜMµèyD°ë¡uæXËÅùì‰¯6wJ“ıø\êvŒ0Ÿl@²Í.…ø¿2İøxDBTí„À‹Ì²Öâ†aSÜšşmoìxüeÅ‡ìRK@&íƒoûÌdÑ~û<Í-T8ÏŠ‰¾Ğ0Éı *JÆÔòfV{›	ßZ(çÙÒ|øÇ Çf*¡‰“ä¸îhp›ÕuÙõ>!ûÍ€ŸŠí¶qFi·ÿØW4¬¿ÅÎ2©Ê,ôA±ëx…ƒ?#°¶µˆØó&°»éì®=kë¯ÔÅã"Sæ¡gjQ>£E"%ÀZíb^üæóTÕ/ªM"z¸÷ä  ¼şå>M¨¬òFZ:çÛ¾ş·Ş®á¶&oÿ;mµœLÔ(
ƒ4yD·"4îä±, ÆXùÊ¶!ºcĞYs×j\96ı|Öük:m&W"ë`?á	í ÜÌ*&¶Šé$_­ƒ0Mbä0#â‹õÚp1/éQ•Óö‘Á÷yÇœôQŠ,şm½«:ZNÏ¶¤é¡p‰¾ûöm°®[Õ’‘é¬IÕz¬Vó¿	røQ‹ªÛ¤b*	¾‚£¯}Ìù³ä³Ü7vàÚiÖ…ªw¶Ÿí–¤,2í¶©Z^Oã‡åëÊs;é+¨*Ë¢_øÒ)Ss	FÌƒİ÷îÌ
é+ò}+*Ÿs?cÅ’”Aâ|1;+WëõÊ‰¾²Qd«ë—/ƒğwyÉp~ÀÏıV8Ÿ°v±Å¢b¾j„éï¢Š»¹-äódŒ•ù43~Yáû©ËšA˜~ûc–ƒ&ù¡©ÖY³Ü¸ÒëÍOÇkIÏD¬‰P›ìD<}±¯§++#¯DH.3•i›4RÇ–ùw‰”(“OÑè¬ `ğ­Í €»êğzV­ºNÇ®0ˆß§É!$’ıT{Ç>”eËbËÍwÑEP:ƒŞ‘ä 1…"»e†ƒ.Êò,»—òı2›Pp,•,›€X>v[Ñ”sÎÜ9óz«ëÓdbİ>ÄÂ yLKO\(;É} ğôşØ£& pM fáºé ™õÈ°µUŒ‚	ªŒÀÊ/]ÃûÛÄyà‰~¿{€U \` ï¦¶ÆĞûËúè	6¯TÿöåÒf#L7ˆø(Cé–PÕ¸æ×M-³D‡6
«fà®f“u“aØé¡XÌN©³"<&ÁÏ¡Ëö2¤şÑ—çş‰•Hª*U´ãïqèÖìí²=°)HÆR!ö$¯„Ø·í22*Œştõ×a”’ÛıÌMhÍÉ‰ª(Ayî5N
¦Òw”•¥÷m³e‚ªTSªHµ”˜›ÜÿŞJ;XoŒô8Ã_ÙÏ›ØüLu¤›‰¶º ÷Ì:²Y|i™^&r ²ôÒGï‘únJ£ª/œI°LĞmŠ¬’l]–º [è>¶‚¨¾QÜ¡-ÕùÑ^;õ'¸H©ÛŸ³>¦›AcâU'1pR0‡&@uà/t…ş¨Üôo27G–ªu]ñ#ríä“êçDU¡±şšÁ.8f±k­Dã”%ğ:sŒ éCƒ°±s#sOª¶ä÷LTu~ñòÔ’‘«à¨½~÷íƒˆbİÎ.WÇÉHidÌÇ<EÜK|Q‰DĞWWç–ÚQ_ÙI+ô
~÷S÷VÊìb´‹YÔYé¸¦hşJªHs2ça7CÎbîLŞãÑ"sş=¬*ƒÆ¨ ğÈ$ƒPæ:-Î
-¢z€yÉD$18–d9›ÈÇ€Áİş¾¬ÏÊºÔ6DƒÇ¹²éh™ûŞ:GnÍu„1µbÁöKÖÍTÅËIÆ;v:PÖ·ÅÂÏ(¥onù'jÿ‹¾[õ¿á‚€®˜Ç°Ë†LY°n°VıaYl¡“B®ó›„¤>8"øou£8à.êÔuš/p$Í3ì™öª‹
Ğ·+c—¡el?)­©â9Î$/‹F»Â^<N„ŞÇÃŞå¹vŞsÚpÓ1>KÄ=AÙ},ŞÖ»`/[é.ÂşdtªÖ79e¨[_Ñ¸¤À‘y¹äfü³ßÆÏÄ¢LAê¯@)"„ÜœX›²Cd[LâÊŞTP»x†Úélùj“d-²0¼eZ˜öø‹¯üû0Lo^–Y¼<à4U4ÿ™ã]Pºì…Y_(¬*6@)İ•²´Ô‘¸	6…÷Ì"ŞP[å
¶\B×ô¯¿—™CNÑXòm[v€ºˆÉš2­_ªEËO–´bÁ
òíAR3Cã¸O•ÀÍwû·¤vó¯ëÜæ.±º7(ıS:TÈ¸ËÎĞìE$âå¬«Lµµ›¦šén6bfgş¹(K››Éá¿¯Ú„	!$™Êäå‡¨7ä’ˆÒÛ(|ŠŸ«+®,Á—|ĞlÑ=;-şP³Ş8?¤Œ°>¨eÕõh{ˆš¯–QF("RŸ*[ËMÿaÒ¿5z“n'‹œû’Ïï’Ul›/ÂÚ„Ô.ÂÜãÄ†Ù$ºıNcà”ÊµJbM,Ÿ6Õ<ßñnÏ´z´;÷P-ë7ĞJîŞùt„HBA‡áÅçç Xévl“ÿJõj%?ÎIIv‹†‘›4Õ¿=l'*‹­E”+)€®¼¼ø|‚g-;Â$Ä6Âú€yk•Û*?ÓÔcš@Å€màËL±6“Ó%Úàišdğ‰/)í+şo±ù3 åpõÁ—ÿôœ%vŞOÁ £šµ-“pÖüçïÌVMØáŞ¿zU>ˆ&yÅ‘Úüb––!±‡úôê”İ(ú[Õ¿®CÜµùÈx^Ãu¤Ñ;İ=7ÿ¼²$@Æ’õ,0Â$Å«cĞã©VÍ^³º½ 3·,3&ZÑ=÷ƒ&v ˜(Çœ49ˆYgë¸Ö˜|åªšªôgß6eS„RësŒÃZˆ>5Ì±|ê-ë8ò¾[èE®ƒd3 °d.$ eì¥·Ô(áN+5®–ÏW¥ı–y7[÷BaÅdóù‡ºY«³1Ï*J2µ\ìıD³©!P2èî®´Ñº¤?Î²`Ú˜òe!²«¡YzœGå[ê7q¦sˆ­ZOœü;ÅÇ¶}Õ›*‘©ÒòJnp‚j äŠÿ	¹şÁ‘ú°*S«úäX–õk:XkfÅYUDÁ×_eSÁw¨Å"»¨Ë
UÀ£¸I¬Óô©§Uö@4‡>-üÒÚ¬Oš½Ó¿5[>İÏÁs€É_ìÃv½È°h~'Y1XÅŸÚ"Œ‘(¤	§8TzW5Í{Â+ÚB×Á;2ç
®ŞÁT%(Sñ#}ºıçx ¿¥89’Uà¿5#ê.Z©ä’¿ÈƒÇ¶‡¸Ç-qŠt¿:†î´N9<'
ml¾LùY½,Ú0UN=¥v­p³Áßğ –A„§}üÌ~µf¦G‹ŸÙ«|7ßÍˆ	©¥,vÖ'ºğ¬ÔKuáge@”úŞ–µV†ØB5tz~eT9XµI‰”'FUô+éÈ–
'˜?$s„ôcÙBãÙTŞ\w}¬N]Uú1üCHkÜÂ1ÚBÜèrÇ„´¬®?{AUëGCv>‹´Qv¯c=µ&EGŒJl)…°ëÑª©ĞëLp[àn¾>m?ÄSÌ7V|Ûö@Cø5Å—	•8æãã^%¡òAİìqi9Nv–e]$ê\Òš¿Í ¨‚œA3Àâ>ZàÿÔßø@rƒ”¤¦,àã…vn+ái™Ö•Šjº¬-é<ÔgÛ=_¢#ŸCcDR‚Hüj@e1ê1¸İv‹õÏ·‡2Ù¿ŸÃJ‹Õ‹é¬i1¢+aòM`’ªì–Òñ“@ì¼ÍKÎÛç(sh%İ<µ‡X&’™	çÔüa¬ö^)Áoë)<^¡ıÈPÑß³ëğ”;y³ª?xÉØtõ„)Æàr0ˆâŠÛ5³UEo>K‚iñAë€…Vq&Ğ½Â'^¿šbá¦+š2ëpi":jn«H¨ì…5ªN\†•…ÑzIµkxï¯_ù*”7ØÜ$M5Oú¨–µaü>‘ç[m3ªöpy@uŒ…çX²£€À¤ÆÀ‡÷S=–ÁßÖ'P	÷ Å@c²°ğ|ZXĞ67ûlë¯ßT‘×~¯w³Zşe³.
Öì+'­ï¬D„ÔK£¸mÉ“vcnÁÇf
ŞS¸’‹J¸bo^(|ßHdÊÎù°dás0ø·jæ·:á#7
òÙò©(ı„¹80İ›Èé¦ÉT|ôy&lK› šò•V yš«?Î!*ÈƒgmÊ¨ ~7w–Œ›NŒ1È÷ğÉ û~şC!‡ÍM"oÀ¾zpáó5tà7·ıÖ¼¤àÍ<Ó&ÇD>âŠMLE©B9Ç‡ø€í ØÁ
?/ÜÙ$öu9ƒ€÷Ü&öµ¿‘†£m}ïÌXæ?u¢Ø#×C¿ªLoc­nùœC¨´Åµ}Ğ
˜çíšĞy9şÆvLtšB¡¢	9Jm³G“ß¹eKıù²KlDOÓœCí“eÑ—N£Lw¶¢ŸÜ
›(‹Eıü5bù…![®«æ€E_Ÿ¤2¡_ÈÂ–=ÆÙq§ii:6D3UUÂ.dÎÁ‚]TRu¢Ğciı¦à^¥ê0°ñü1êOmşùÂhÇ!èJ‚“Å},Á·Ç».—¯¤Æ7lô‰}S–á{õµW5Ó2Á.ª’…¹Å2	×š;â6`½„	‘¶ÚE=2Ú“íĞ	›éäœşOÑ9(r^‰+{)iÇJ ã%ø("¬Šz"ïú9H
@çÍısF…SPÿÕúôSº¼éC1†ÉtÌ(Š¬ƒ¹ç²"«U-z‰±è£{GÎqH×ãi`_z,tç‚cÉ ªp½h­OvPc=Y\È›E€í™HÁû™Á1hÀÚzd§û<¸à™Qv[»”n…³òsÙ¢štœù‘H
~}b…à×á!p€-^„gK…Hø;¼“:t³xµ2?£Ï_sÓM]]K{DÛ@MQ¤ÚÖé ’Fo“tƒnüAè’×ˆ]Ä9‰	Å»‘%ãüJ«ÚøTpícmÔÄË³H5x‡©¦’FóH½#/cíËf˜¥%îmêæ/çóD¬oÁ È!o€kÔëc¼š	1ëB-	à£Í¶éçB_	34Ñ€îZø§7J„;_BoÊcÇQ§zŞDf«¸BZf_ıĞjgêaTÿÛ°øİ%jl‘^ÛAÎ˜ÇÊe,4ÄhÔ—í(“º·şí1ÅÑ×eTò¤}õ°
«wkÏ=Wrk{ñ¦YÍdÀ	x2ºQ¨¶PØ°±Ÿ=ïëÑw¡ÊM„¤}ŒÕ.lé¾ Rİ›ÉŒ×3‡vÊğ·éMğ¹»j—H{W«Y™‚MÿôhUTß[tk”“¶lçù¨oÔ„‚ç–nC3zŞ4c;ã¸K­NÅrûèŒZô¾âNt‰³ ï²§İ9­üU7­\ÎÓßauc)°½ö¦vçÙ]qÚZi¯²ÒØ€!š.iëæxÊ9.6?áæ?¶˜Ğ—)c°~‰›}—¢q€ş³¿)ï÷œP­·ôj øÂ›H3¿Nª8îÜI`~@€D]óÕFî€­=«M²H’x„g©<oˆkBÔ‚áZ‹döe~³³ÂsLŒQiñY*pDGf­3¿8†c³·
§4‹”|9k<nªILyzí¨P›œ'Wï¿{pİ?èlå
Ò%ÃqŒ@Ÿ§å™ÖˆÙF0mñ«Âiš2Ã%–Ø*İä­<YŞñ?=u?B±è–p~OĞ¦¨Ø'®¢ÿ[NùàG”r:Z%öGÙš‹V¤ÿ1yÌÓTçî9˜$tÌ;¯.MaƒŒ$ït+EHí¥¹¦bœáÄykV’‘(}J¦ú¿#ÃÃ€pGÿÎƒ·È³¹d»NõËÖÖDèÕCFôv:ÉœUAjÓæ±šå¢ÉßìíÙf3– ³8k/kèŠdÒfrµcÊ»qô8	J£Ğh†p‰÷âf"P4*—òÕ\½nkÅF>–t?Šñ0GÜaÍá¢˜ËÊ¤Oì©Çœcƒ¥j` á&D;4#¡õÒ$=ôpLKDQtÜ÷İ5§nÌæÆu3Æ¥Ş¡—Ö¶Üƒ$ÖÉ4‡Å’HßXå4Ó£¡d[²›­#ê¥q¶†¶7öÖ*a:ÃÁmë{f6ç£U?>r?e±t÷1ÉøUİ<÷úáU>øjÃt	ğÑ¡Ÿ}ÜkèŸIÑé}éÒØSÚ¿ù$«Ş?8=qésîÈû× ^
´9{ãƒ8Øô›wL€ºÈ\ÏjêÃ®‰„œpı¥Dm¼ÁJµÆG¾v?4eºšØâi§³Õœéî)]/gşl(/Ã²ûØş¯(…v‡goÛ)ÔkĞ?Æ©X¹¨ı5±Y¹ô¾…ÊÛ_ugGp¹