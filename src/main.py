#!/usr/bin/env python3

import os
import shutil
import boto3
import certbot.main
import re
from datetime import datetime

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
        print('Certificate Not After ')
        print(response['Certificate']['NotAfter'])
        print(f'Cert renew will be performed after')
        print(need_renew_date)
        if (datetime.now() > need_renew_date): return False
        return True
    except Exception as e:
        print(f'Exception - {e}')
        print(f"Could not get certificate {cert_arn}, or check its renewal date...")
        return False

def update_acm(acm_client, domains, cert_arn):
    cert_dir = os.path.join(os.path.join(CERTBOT_DIR, 'live'), domains.split(',')[0])
    cert_dir = re.sub("\.$", "", cert_dir)
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
    
def guarded_handler(event, context):
    # Contact email for LetsEncrypt notifications
    email = os.environ.get('EMAIL')
    # Domains that will be included in the certificate
    domains = os.environ.get('DOMAINS')
    # Certificate ARN in ACM to update to 
    cert_arn = os.environ.get('CERT_ARN')

    #Initialize boto3 clients
    acm_client = boto3.client('acm')
    # s3_client = boto3.client('s3')

    if (not acm_cert_is_valid(acm_client, cert_arn)):
        try:
            obtain_certs(email, domains)
            update_acm(acm_client, domains, cert_arn)
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
