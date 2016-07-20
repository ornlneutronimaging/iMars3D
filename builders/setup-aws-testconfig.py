#!/usr/bin/env python

import os, sys

CONFIG="""[profile imars3d_tester]
output = text
region = us-east-1
"""

CRED_template="""[imars3d_tester]
aws_access_key_id = %(id)s
aws_secret_access_key = %(secret)s
"""

dir = os.path.expanduser("~/.aws")
if not os.path.exists(dir):
    os.makedirs(dir)

config_path = os.path.join(dir, "config")
if os.path.exists(config_path):
    raise IOError("%s already exists" % config_path)
open(config_path, 'wt').write(CONFIG)


id = os.environ['AWS_S3_ACCESS_ID']
secret = os.environ['AWS_S3_ACCESS_SECRET']
cred_path = os.path.join(dir, "credentials")
if os.path.exists(cred_path):
    raise IOError("%s already exists" % cred_path)
open(cred_path, 'wt').write(CRED_template % locals())
