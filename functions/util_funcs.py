
def get_email_code(): 
    return input("Please input your 4-digit code sent to your email!")

def clean(s):
    return " ".join(s.replace("\n", " ").split())