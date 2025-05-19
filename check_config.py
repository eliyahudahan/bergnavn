from backend.config.config import Config

def check_env_config():
    print("🔍 Checking environment configuration...\n")

    required_vars = {
        'SECRET_KEY': Config.SECRET_KEY,
        'SQLALCHEMY_DATABASE_URI': Config.SQLALCHEMY_DATABASE_URI,
        'DEBUG': Config.DEBUG,
        'MAIL_SERVER': Config.MAIL_SERVER,
        'MAIL_PORT': Config.MAIL_PORT,
        'MAIL_USE_TLS': Config.MAIL_USE_TLS,
        'MAIL_USE_SSL': Config.MAIL_USE_SSL,
        'MAIL_USERNAME': Config.MAIL_USERNAME,
        'MAIL_PASSWORD': Config.MAIL_PASSWORD,
    }

    all_good = True
    for key, value in required_vars.items():
        if value is None or value == "":
            print(f"❌ {key} is MISSING or EMPTY!")
            all_good = False
        else:
            print(f"✅ {key} = {value}")

    print("\n✅ Check complete." if all_good else "\n⚠️  Some values are missing — please check your .env file.")

if __name__ == "__main__":
    check_env_config()
