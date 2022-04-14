#!/usr/bin/env python3

import os
import shutil
import boto3
import certbot.main
import re
from datetime import datetime, date

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


# # /tmp/certbot
# # ├── live
# # │   └── [domain]
# # │       ├── README
# # │       ├── cert.pem
# # │       ├── chain.pem
# # │       ├── fullchain.pem
# # │       └── privkey.pem
# def upload_certs(s3_client, s3_bucket, s3_prefix):
#     cert_dir = os.path.join(CERTBOT_DIR, 'live')
#     for dirpath, _dirnames, filenames in os.walk(cert_dir):
#         for filename in filenames:
#             local_path = os.path.join(dirpath, filename)
#             relative_path = os.path.relpath(local_path, cert_dir)
#             s3_key = os.path.join(s3_prefix, relative_path)
#             print(f'Uploading: {local_path} => s3://{s3_bucket}/{s3_key}')
#             s3_client.upload_file(local_path, s3_bucket, s3_key)

# # https://code-examples.net/en/q/1e70b70
# def download_cert_s3(s3_client, s3_bucket, s3_prefix, domains):
# # certbot-lambda-certificates-4-test-voximplant-com/4-test-voximplant-com/4.test.voximplant.com/cert.pem
# # {   bucket                                      }/{ prefix            }/{     domains     }/
#     domains = re.sub("\.$", "", domains)
#     target = os.path.join(CERTBOT_DIR, 'live')
#     #s3_path = os.path.join(s3_prefix, domains)
#     s3_path = s3_prefix

#     # Handle missing / at end of prefix
#     if not s3_path.endswith('/'):
#         s3_path += '/'

#     paginator = s3_client.get_paginator('list_objects_v2')
#     for result in paginator.paginate(Bucket=s3_bucket, Prefix=s3_path):
#         # Download each file individually
#         for key in result['Contents']:
#             # Calculate relative path
#             rel_path = key['Key'][len(s3_path):]
#             # Skip paths ending in /
#             if not key['Key'].endswith('/'):
#                 local_file_path = os.path.join(target, rel_path)
#                 # Make sure directories exist
#                 local_file_dir = os.path.dirname(local_file_path)
#                 if not os.path.exists(local_file_dir):
#                     os.makedirs(local_file_dir)
#                 print(f'Downloading {key} to {local_file_path}')
#                 s3_client.download_file(s3_bucket, key['Key'], local_file_path)

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
    cert_dir = os.path.join(os.path.join(CERTBOT_DIR, 'live'), domains)
    cert_dir = re.sub("\.$", "", cert_dir)
    
    certificate=open(os.path.join(cert_dir, 'cert.pem'), 'rb').read()
    privatekey=open(os.path.join(cert_dir, 'privkey.pem'), 'rb').read()
    chain=open(os.path.join(cert_dir, 'chain.pem'), 'rb').read()

    try:
        response = acm_client.describe_certificate(CertificateArn=cert_arn)
        print('Certificate Not After - ' + response['Certificate']['NotAfter'])
        response = acm_client.import_certificate(
            CertificateArn=cert_arn,
            Certificate=certificate,
            PrivateKey=privatekey,
            CertificateChain=chain
        )
    except:
        print(f'Can not get cert {cert_arn}. Uploading as new cert to ACM...')
        response = acm_client.import_certificate(
            Certificate=certificate,
            PrivateKey=privatekey,
            CertificateChain=chain
        )
    print(f'Certificates uploaded to ACM successfully. {response}')
    
def guarded_handler(event, context):
    # Contact email for LetsEncrypt notifications
    email = os.environ.get('EMAIL')
    # Domains that will be included in the certificate
    domains = os.environ.get('DOMAINS')
    # # The S3 bucket to publish certificates
    # s3_bucket = os.environ.get('S3_BUCKET')
    # # The S3 key prefix to publish certificates
    # s3_prefix = os.environ.get('S3_PREFIX')
    # Certificate ARN in ACM to update to 
    cert_arn = os.environ.get('CERT_ARN')

    #Initialize boto3 clients
    acm_client = boto3.client('acm')
    # s3_client = boto3.client('s3')

    if (not acm_cert_is_valid(acm_client, cert_arn)):
        try:
            obtain_certs(email, domains)
        #     upload_certs(s3_client, s3_bucket, s3_prefix)
        # except Exception as e:
        #     print('Obtaining and uploading certificate failed...')
        #     print(f'Exception - {e}')
        #     try:
        #         download_cert_s3(s3_client, s3_bucket, s3_prefix, domains)
        #     except Exception as e:
        #         print('Downloading certificate from S3 failed...')
        #         print(f'Exception - {e}')
        # try:
            update_acm(acm_client, domains, cert_arn)
        except Exception as e:
            print('Updating cert in ACM failed...')
            print(f'Exception - {e}')        

    return 'Certificates obtained and uploaded successfully.'


def lambda_handler(event, context):
    try:
        rm_tmp_dir()
        return guarded_handler(event, context)
    finally:
        rm_tmp_dir()
