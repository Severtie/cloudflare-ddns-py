import requests
import os
import json
import dotenv

def fetch_current_ip() -> str:
    file_name = "last_ip.txt"
    if not os.path.isfile(file_name):
        with open(file_name, 'w') as file:
            file.write("")
            return ""
    with open(file_name, 'r') as file:
        return file.read()
    
def save_current_ip(ip: str):
        file_name = "last_ip.txt"
        with open(file_name, 'w') as file:
            file.write(ip)

def fetch_ip_address() -> str:
    ip = requests.get('https://api.ipify.org').content.decode('utf8')
    return str(ip)

def set_cloudflare_ip(ip: str) -> bool:
    cl_zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
    cl_record_id = os.getenv("CLOUDFLARE_RECORD_ID")
    cl_api_key = os.getenv("CLOUDFLARE_API_KEY")
    cl_record_name = os.getenv("CLOUDFLARE_RECORD_NAME")
    
    body = {"type": "A", "name": cl_record_name, "content": ip}
    headers = { "Authorization": f"Bearer {cl_api_key}", "Content-Type": "application/json"}
    url = f"https://api.cloudflare.com/client/v4/zones/{cl_zone_id}/dns_records/{cl_record_id}"

    resp = requests.patch(url, json.dumps(body), headers=headers)
    if resp.status_code != 200:
        # inform user
        print("Failed to set DNS record:")
        print(f"status code: {resp.status_code}\n body: {resp.content}")
        return False
    return True

def get_send_notification_env() -> bool:
    should_send_notification = False
    try:
        should_send_notification = bool(os.getenv("SEND_GOTIFY_NOTIFICATION"))
    except KeyError:
        should_send_notification = False
    return should_send_notification

def send_gotify_notification(succeeded: bool, old_ip: str, new_ip: str):
    token = os.getenv("GOTIFY_TOKEN")
    server = os.getenv("GOTIFY_URL")
    url = f"{server}/message?token={token}"
    succeeded_text =  "succeeded" if succeeded else "did not succeed"
    body = {"message":f"Public IP is changed from {old_ip} to {new_ip}. The action to change the DNS record {succeeded_text}", "priority":0, "title":"Public IP changed"}
    resp = requests.post(url, json=body)
    if resp.status_code != 200:
        print("Failed to send Gotify notification:")
        print(f"status code: {resp.status_code}\n body: {resp.content}")

def main():
    dotenv.load_dotenv()
    current_set_ip = fetch_current_ip()
    new_ip = fetch_ip_address()
    if current_set_ip != new_ip:
        print("New IP detected!")
        succeeded = set_cloudflare_ip(new_ip)
        if succeeded:
            print("Setting DNS record succeeded")
            save_current_ip(new_ip)
        send_notification = get_send_notification_env()
        if(send_notification):
            send_gotify_notification(succeeded, current_set_ip, new_ip)
    else:
        print("No new public IP assigned")


if __name__ == "__main__":
    main()
