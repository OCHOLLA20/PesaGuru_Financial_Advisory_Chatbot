import base64
import json
import logging
import os
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mpesa_api')

class MpesaAPI:
    """
    Class to handle M-Pesa API integrations for PesaGuru
    """
    
    # API endpoints
    SANDBOX_BASE_URL = "https://sandbox.safaricom.co.ke"
    PRODUCTION_BASE_URL = "https://api.safaricom.co.ke"
    
    # API endpoints
    OAUTH_URL = "/oauth/v1/generate?grant_type=client_credentials"
    C2B_REGISTER_URL = "/mpesa/c2b/v1/registerurl"
    B2C_URL = "/mpesa/b2c/v1/paymentrequest"
    TRANSACTION_STATUS_URL = "/mpesa/transactionstatus/v1/query"
    ACCOUNT_BALANCE_URL = "/mpesa/accountbalance/v1/query"
    STK_PUSH_URL = "/mpesa/stkpush/v1/processrequest"
    STK_QUERY_URL = "/mpesa/stkpushquery/v1/query"
    
    def __init__(self, env="sandbox"):
        """
        Initialize the MpesaAPI class
        
        Args:
            env (str): Environment to use - "sandbox" or "production"
        """
        self.env = env
        
        # Set the base URL based on environment
        self.base_url = self.SANDBOX_BASE_URL if env == "sandbox" else self.PRODUCTION_BASE_URL
        
        # Get credentials from environment variables
        if env == "sandbox":
            self.consumer_key = os.getenv("MPESA_CONSUMER_KEY_SANDBOX")
            self.consumer_secret = os.getenv("MPESA_CONSUMER_SECRET_SANDBOX")
            self.shortcode = os.getenv("MPESA_SHORTCODE_SANDBOX")
            self.passkey = os.getenv("MPESA_PASSKEY_SANDBOX")
        else:
            self.consumer_key = os.getenv("MPESA_CONSUMER_KEY")
            self.consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")
            self.shortcode = os.getenv("MPESA_SHORTCODE")
            self.passkey = os.getenv("MPESA_PASSKEY")
        
        # Initialize access token
        self.access_token = None
        self.token_expiry = 0  # Unix timestamp
        
        # Callback URLs (should be configurable)
        self.callback_url = os.getenv("MPESA_CALLBACK_URL", "https://pesaguru.com/api/callbacks/mpesa")
        self.timeout_url = os.getenv("MPESA_TIMEOUT_URL", "https://pesaguru.com/api/callbacks/mpesa/timeout")
        
        logger.info(f"Initialized M-Pesa API in {env} environment")
    
    def _get_auth_token(self):
        """
        Get OAuth access token from M-Pesa API
        
        Returns:
            str: Access token
        """
        # Check if we have a valid token already
        current_time = int(time.time())
        if self.access_token and current_time < self.token_expiry:
            return self.access_token
        
        try:
            # Prepare auth credentials
            auth_string = f"{self.consumer_key}:{self.consumer_secret}"
            auth_bytes = auth_string.encode("ascii")
            auth_b64 = base64.b64encode(auth_bytes).decode("ascii")
            
            # Set headers
            headers = {
                "Authorization": f"Basic {auth_b64}"
            }
            
            # Make API request
            url = f"{self.base_url}{self.OAUTH_URL}"
            response = requests.get(url, headers=headers)
            
            # Process response
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                # Token typically expires in 1 hour, but we'll set it to expire in 50 minutes to be safe
                self.token_expiry = current_time + 3000  # 50 minutes
                return self.access_token
            else:
                logger.error(f"Failed to get auth token: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting auth token: {str(e)}")
            return None
    
    def _generate_password(self, timestamp):
        """
        Generate a base64 encoded password for STK push
        
        Args:
            timestamp (str): Current timestamp in YYYYMMDDHHmmss format
        
        Returns:
            str: Base64 encoded password
        """
        password_str = f"{self.shortcode}{self.passkey}{timestamp}"
        password_bytes = password_str.encode("ascii")
        return base64.b64encode(password_bytes).decode("ascii")
    
    def initiate_stk_push(self, phone_number, amount, reference, description="PesaGuru Payment"):
        """
        Initiate an STK push request to a customer's phone
        
        Args:
            phone_number (str): Customer phone number (format: 254XXXXXXXXX)
            amount (int): Amount to charge
            reference (str): Payment reference
            description (str, optional): Transaction description
        
        Returns:
            dict: API response
        """
        # Get auth token
        token = self._get_auth_token()
        if not token:
            return {"error": "Could not get authentication token"}
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Generate password
        password = self._generate_password(timestamp)
        
        # Format phone number (remove leading 0 or +254)
        if phone_number.startswith("+"):
            phone_number = phone_number[1:]
        if phone_number.startswith("0"):
            phone_number = "254" + phone_number[1:]
        
        # Prepare request data
        data = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": reference,
            "TransactionDesc": description
        }
        
        # Set headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Make API request
            url = f"{self.base_url}{self.STK_PUSH_URL}"
            response = requests.post(url, json=data, headers=headers)
            
            # Process response
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"STK push failed: {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"Error initiating STK push: {str(e)}")
            return {"error": str(e)}
    
    def check_stk_push_status(self, checkout_request_id):
        """
        Check the status of an STK push transaction
        
        Args:
            checkout_request_id (str): Checkout request ID from STK push response
        
        Returns:
            dict: API response
        """
        # Get auth token
        token = self._get_auth_token()
        if not token:
            return {"error": "Could not get authentication token"}
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Generate password
        password = self._generate_password(timestamp)
        
        # Prepare request data
        data = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }
        
        # Set headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Make API request
            url = f"{self.base_url}{self.STK_QUERY_URL}"
            response = requests.post(url, json=data, headers=headers)
            
            # Process response
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"STK status check failed: {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"Error checking STK status: {str(e)}")
            return {"error": str(e)}
    
    def check_transaction_status(self, transaction_id, command="TransactionStatusQuery"):
        """
        Check the status of a transaction
        
        Args:
            transaction_id (str): Transaction ID
            command (str, optional): Command ID
        
        Returns:
            dict: API response
        """
        # Get auth token
        token = self._get_auth_token()
        if not token:
            return {"error": "Could not get authentication token"}
        
        # Prepare request data
        data = {
            "Initiator": os.getenv("MPESA_INITIATOR_NAME", "testapi"),
            "SecurityCredential": os.getenv("MPESA_SECURITY_CREDENTIAL", ""),
            "CommandID": command,
            "TransactionID": transaction_id,
            "PartyA": self.shortcode,
            "IdentifierType": "4",  # Shortcode
            "ResultURL": self.callback_url,
            "QueueTimeOutURL": self.timeout_url,
            "Remarks": "Transaction status check",
            "Occasion": ""
        }
        
        # Set headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Make API request
            url = f"{self.base_url}{self.TRANSACTION_STATUS_URL}"
            response = requests.post(url, json=data, headers=headers)
            
            # Process response
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Transaction status check failed: {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"Error checking transaction status: {str(e)}")
            return {"error": str(e)}
    
    def check_account_balance(self, command="AccountBalance"):
        """
        Check account balance
        
        Args:
            command (str, optional): Command ID
        
        Returns:
            dict: API response
        """
        # Get auth token
        token = self._get_auth_token()
        if not token:
            return {"error": "Could not get authentication token"}
        
        # Prepare request data
        data = {
            "Initiator": os.getenv("MPESA_INITIATOR_NAME", "testapi"),
            "SecurityCredential": os.getenv("MPESA_SECURITY_CREDENTIAL", ""),
            "CommandID": command,
            "PartyA": self.shortcode,
            "IdentifierType": "4",  # Shortcode
            "Remarks": "Account balance query",
            "QueueTimeOutURL": self.timeout_url,
            "ResultURL": self.callback_url
        }
        
        # Set headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Make API request
            url = f"{self.base_url}{self.ACCOUNT_BALANCE_URL}"
            response = requests.post(url, json=data, headers=headers)
            
            # Process response
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Account balance check failed: {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"Error checking account balance: {str(e)}")
            return {"error": str(e)}
    
    def register_c2b_urls(self, confirmation_url=None, validation_url=None, response_type="Completed"):
        """
        Register C2B URLs
        
        Args:
            confirmation_url (str, optional): Confirmation URL
            validation_url (str, optional): Validation URL
            response_type (str, optional): Response type ('Completed' or 'Canceled')
        
        Returns:
            dict: API response
        """
        # Get auth token
        token = self._get_auth_token()
        if not token:
            return {"error": "Could not get authentication token"}
        
        # Use default URLs if not provided
        if not confirmation_url:
            confirmation_url = os.getenv(
                "MPESA_CONFIRMATION_URL", 
                "https://pesaguru.com/api/callbacks/mpesa/confirmation"
            )
            
        if not validation_url:
            validation_url = os.getenv(
                "MPESA_VALIDATION_URL", 
                "https://pesaguru.com/api/callbacks/mpesa/validation"
            )
        
        # Prepare request data
        data = {
            "ShortCode": self.shortcode,
            "ResponseType": response_type,
            "ConfirmationURL": confirmation_url,
            "ValidationURL": validation_url
        }
        
        # Set headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Make API request
            url = f"{self.base_url}{self.C2B_REGISTER_URL}"
            response = requests.post(url, json=data, headers=headers)
            
            # Process response
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"C2B URL registration failed: {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"Error registering C2B URLs: {str(e)}")
            return {"error": str(e)}
    
    def b2c_payment(self, phone_number, amount, command_id="BusinessPayment", remarks="", occasion=""):
        """
        Send money from business to customer (B2C)
        
        Args:
            phone_number (str): Customer phone number (format: 254XXXXXXXXX)
            amount (int): Amount to send
            command_id (str, optional): Command ID
            remarks (str, optional): Transaction remarks
            occasion (str, optional): Transaction occasion
        
        Returns:
            dict: API response
        """
        # Get auth token
        token = self._get_auth_token()
        if not token:
            return {"error": "Could not get authentication token"}
        
        # Format phone number (remove leading 0 or +254)
        if phone_number.startswith("+"):
            phone_number = phone_number[1:]
        if phone_number.startswith("0"):
            phone_number = "254" + phone_number[1:]
        
        # Prepare request data
        data = {
            "InitiatorName": os.getenv("MPESA_INITIATOR_NAME", "testapi"),
            "SecurityCredential": os.getenv("MPESA_SECURITY_CREDENTIAL", ""),
            "CommandID": command_id,
            "Amount": amount,
            "PartyA": self.shortcode,
            "PartyB": phone_number,
            "Remarks": remarks if remarks else "B2C Payment",
            "QueueTimeOutURL": self.timeout_url,
            "ResultURL": self.callback_url,
            "Occasion": occasion
        }
        
        # Set headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Make API request
            url = f"{self.base_url}{self.B2C_URL}"
            response = requests.post(url, json=data, headers=headers)
            
            # Process response
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"B2C payment failed: {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"Error sending B2C payment: {str(e)}")
            return {"error": str(e)}

    def process_callback(self, callback_data):
        """
        Process M-Pesa callback data
        
        Args:
            callback_data (dict): Callback data from M-Pesa
            
        Returns:
            dict: Processed callback data
        """
        try:
            # Extract the relevant data from the callback
            if "Body" in callback_data and "stkCallback" in callback_data["Body"]:
                stk_callback = callback_data["Body"]["stkCallback"]
                
                # Process STK push callback
                result = {
                    "type": "stk_push",
                    "merchant_request_id": stk_callback.get("MerchantRequestID", ""),
                    "checkout_request_id": stk_callback.get("CheckoutRequestID", ""),
                    "result_code": stk_callback.get("ResultCode", 0),
                    "result_desc": stk_callback.get("ResultDesc", ""),
                    "timestamp": datetime.now().isoformat(),
                    "raw_data": callback_data
                }
                
                # Extract transaction details if successful
                if stk_callback.get("ResultCode", 1) == 0 and "CallbackMetadata" in stk_callback:
                    items = stk_callback["CallbackMetadata"].get("Item", [])
                    for item in items:
                        if item.get("Name") == "Amount":
                            result["amount"] = item.get("Value", 0)
                        elif item.get("Name") == "MpesaReceiptNumber":
                            result["receipt_number"] = item.get("Value", "")
                        elif item.get("Name") == "TransactionDate":
                            result["transaction_date"] = item.get("Value", "")
                        elif item.get("Name") == "PhoneNumber":
                            result["phone_number"] = item.get("Value", "")
                
                logger.info(f"Processed STK push callback: {json.dumps(result, indent=2)}")
                return result
                
            elif "Body" in callback_data and "Result" in callback_data["Body"]:
                result_data = callback_data["Body"]["Result"]
                
                # Process transaction status callback
                result = {
                    "type": "transaction_status",
                    "result_type": result_data.get("ResultType", 0),
                    "result_code": result_data.get("ResultCode", 0),
                    "result_desc": result_data.get("ResultDesc", ""),
                    "transaction_id": result_data.get("TransactionID", ""),
                    "originator_conversation_id": result_data.get("OriginatorConversationID", ""),
                    "conversation_id": result_data.get("ConversationID", ""),
                    "timestamp": datetime.now().isoformat(),
                    "raw_data": callback_data
                }
                
                logger.info(f"Processed transaction status callback: {json.dumps(result, indent=2)}")
                return result
                
            else:
                logger.warning(f"Unknown callback format: {json.dumps(callback_data, indent=2)}")
                return {
                    "type": "unknown",
                    "timestamp": datetime.now().isoformat(),
                    "raw_data": callback_data
                }
                
        except Exception as e:
            logger.error(f"Error processing callback: {str(e)}")
            return {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "raw_data": callback_data
            }


# Example usage
if __name__ == "__main__":
    # Initialize M-Pesa API
    mpesa = MpesaAPI(env="sandbox")
    
    # Example: Initiate STK push
    response = mpesa.initiate_stk_push(
        phone_number="254712345678",
        amount=1,  # Amount in KES
        reference="PesaGuru123",
        description="PesaGuru Investment"
    )
    
    print("STK Push Response:")
    print(json.dumps(response, indent=2))
    
    # If successful, check status after a few seconds
    if "CheckoutRequestID" in response:
        checkout_request_id = response["CheckoutRequestID"]
        
        # Wait for a few seconds
        print("Waiting for 5 seconds before checking status...")
        time.sleep(5)
        
        # Check status
        status_response = mpesa.check_stk_push_status(checkout_request_id)
        
        print("STK Push Status Response:")
        print(json.dumps(status_response, indent=2))
