#!/usr/bin/env python3

import os
import shutil
import boto3
import certbot.main
import re
import zlib
import base64
from datetime import datetime
from cryptography import x509

# Let’s Encrypt acme-v02 server that supports wildcard certificates
CERTBOT_SERVER = 'https://acme-v02.api.letsencrypt.org/directory'

# Temp dir of Lambda runtime
CERTBOT_DIR = '/tmp/certbot'

def rm_tmp_dir():
    if os.path.exists(CERTBOT_DIR):
        try:
            shutil.rmtree(CERTBOT_DIR)
        except NotADirectoryError:
            os.remove(CERTBOT_DIR)

def obtain_certs(email, domains):
    certbot_args = [
        # Override directory paths so script doesn't have to be run as root
        '--config-dir', CERTBOT_DIR,
        '--work-dir', CERTBOT_DIR,
        '--logs-dir', CERTBOT_DIR,

        # Obtain a cert but don't install it
        'certonly',

        # Run in non-interactive mode
        '--non-interactive',

        # Agree to the terms of service
        '--agree-tos',

        # Email of domain administrator
        '--email', email,

        # Use dns challenge with route53
        '--dns-route53',
        '--preferred-challenges', 'dns-01',

        # Use this server instead of default acme-v01
        '--server', CERTBOT_SERVER,

        # Domains to provision certs for (comma separated)
        '--domains', domains,
    ]
    return certbot.main.main(certbot_args)

def acm_cert_is_valid(acm_client, cert_arn):
    try:
        response = acm_client.describe_certificate(CertificateArn=cert_arn)
        cert_exp_date = response['Certificate']['NotAfter']
        need_renew_date = datetime(cert_exp_date.year, cert_exp_date.month - 1, cert_exp_date.day)
        print('Certificate in ACM Not After ')
        print(response['Certificate']['NotAfter'])
        print(f'Certificate renew in ACM will be performed after')
        print(need_renew_date)
        if (datetime.now() > need_renew_date): return False
        return True
    except Exception as e:
        print(f'Exception - {e}')
        print(f"Could not get certificate {cert_arn} from ACM, or check its renewal date...")
        return False

def ssm_cert_is_valid (ssm_client, ssm_param_cert_name):
    try:
        response = ssm_client.get_parameter(Name=ssm_param_cert_name)
        cert_body=base64.b64decode(response["Parameter"]["Value"])
        cert_body=zlib.decompress(cert_body).decode()
        cert = x509.load_pem_x509_certificate(bytes(cert_body, encoding='utf-8'))
        cert_exp_date = cert.not_valid_after
        need_renew_date = datetime(cert_exp_date.year, cert_exp_date.month - 1, cert_exp_date.day)
        print('Certificate in SSM Parameters Store Not After ')
        print(cert_exp_date)
        print('Certificate in SSM Parameters Store renew will be performed after')
        print(need_renew_date)
        if (datetime.now() > need_renew_date): return False
        return True
    except Exception as e:
        print("Checking certificate validity from SSM Parameter Store failed...")
        print(f'Exception - {e}')
        return False

def update_acm(acm_client, cert_dir, cert_arn):
    try:
        certificate=open(os.path.join(cert_dir, 'cert.pem'), 'rb').read()
        privatekey=open(os.path.join(cert_dir, 'privkey.pem'), 'rb').read()
        chain=open(os.path.join(cert_dir, 'chain.pem'), 'rb').read()

        response = acm_client.import_certificate(
            CertificateArn=cert_arn,
            Certificate=certificate,
            PrivateKey=privatekey,
            CertificateChain=chain
        )
        print(f'Certificates uploaded to ACM successfully. {response}')
        return True
    except Exception as e:
        print(f'Exception - {e}')
        return False

def update_ssm(ssm_client, cert_dir, ssm_param_cert_name, ssm_param_key_name, ssm_param_chain_name):
    print("Trying to put certificate files to Parameter Store...")
    try:
        certificate = open(os.path.join(cert_dir, 'cert.pem'), 'r').read()
        certificate = zlib.compress(certificate.encode('ascii'),level=-1)
        certificate = base64.b64encode(certificate).decode()

        privatekey = open(os.path.join(cert_dir, 'privkey.pem'), 'r').read()
        privatekey = zlib.compress(privatekey.encode('ascii'),level=-1)
        privatekey = base64.b64encode(privatekey).decode()

        chain = open(os.path.join(cert_dir, 'chain.pem'), 'r').read()
        chain = zlib.compress(chain.encode('ascii'),level=-1)
        chain = base64.b64encode(chain).decode()

        print(f"Putting Certificate to {ssm_param_cert_name}...")
        response = ssm_client.put_parameter(
            Name=ssm_param_cert_name,
            Value=certificate,
            Type="String",
            Overwrite=True,
            Tier='Advanced'
            )
        print("Certificate parameter record renewed sucessfully...")

        print(f"Putting Private Key to {ssm_param_key_name}...")
        response = ssm_client.put_parameter(
            Name=ssm_param_key_name,
            Value=privatekey,
            Type="String",
            Overwrite=True,
            Tier='Advanced'
            )
        print("Private Key parameter record renewed sucessfully...")
        
        print(f"Putting Chain to {ssm_param_chain_name}...")
        response = ssm_client.put_parameter(
            Name=ssm_param_chain_name,
            Value=chain,
            Type="String",
            Overwrite=True,
            Tier='Advanced'
            )
        print("Certificate Chain parameter record renewed sucessfully...")
    except Exception as e:
        print("Putting certificate to parameter store failed...")
        print(f'Exception - {e}')
        return False
    
def guarded_handler(event, context):
    # Contact email for LetsEncrypt notifications
    email = os.environ.get('EMAIL')
    # Domains that will be included in the certificate
    domains = os.environ.get('DOMAINS')
    # Certificate ARN in ACM to update to 
    cert_arn = os.environ.get('CERT_ARN')
    # SSM Parameter name to store Cettificate
    ssm_param_cert_name = os.environ.get('SSM_PARAMETER_CERT_NAME')
    # SSM parameter name to store Private Key
    ssm_param_key_name = os.environ.get('SSM_PARAMETER_KEY_NAME')
    # SSM parameter name to store Certificate Chain
    ssm_param_chain_name = os.environ.get('SSM_PARAMETER_CHAIN_NAME')

    cert_dir = os.path.join(os.path.join(CERTBOT_DIR, 'live'), domains.split(',')[0])
    cert_dir = re.sub("\.$", "", cert_dir)

    #Initialize boto3 clients
    acm_client = boto3.client('acm')
    # s3_client = boto3.client('s3')
    ssm_client = boto3.client('ssm')

    if ((not acm_cert_is_valid(acm_client, cert_arn)) or (not ssm_cert_is_valid(ssm_client, ssm_param_cert_name))):
        try:
            obtain_certs(email, domains)
            update_acm(acm_client, cert_dir, cert_arn)
            update_ssm(ssm_client, cert_dir, ssm_param_cert_name, ssm_param_key_name, ssm_param_chain_name)
        except Exception as e:
            print('Updating cert in ACM failed...')
            print(f'Exception - {e}')
            return False      

    return 'Certificates obtained and uploaded successfully.'

def lambda_handler(event, context):
    try:
        rm_tmp_dir()
        return guarded_handler(event, context)
    finally:
        rm_tmp_dir()
