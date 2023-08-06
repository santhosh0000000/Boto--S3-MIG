import boto
import os
import shutil

# Set the access and secret keys for the Scality cluster
old_access_key = "Eurofin-Storage2"
old_secret_key = "7ax5Py!dRHL"

# Set the access and secret keys for the new Ceph cluster
new_access_key = "Eurofin-Storage2"
new_secret_key = "7ax5Py!dRHL"

# Connect to the Scality cluster
old_conn = boto.connect_s3(
        aws_access_key_id = old_access_key,
        aws_secret_access_key = old_secret_key,
        host = 'bckconnector.scality.it.cloud.it',
        is_secure=False,
        calling_format = boto.s3.connection.OrdinaryCallingFormat(),
)

# Connect to the new Ceph cluster
new_conn = boto.connect_s3(
        aws_access_key_id = new_access_key,
        aws_secret_access_key = new_secret_key,
        host = '10.151.11.10:80',
        is_secure=False,
        calling_format = boto.s3.connection.OrdinaryCallingFormat(),
)

# Loop through each bucket in the Scality cluster
for bucket in old_conn.get_all_buckets():
    # Print the name of the bucket
    print("Bucket: {}".format(bucket.name))

    # Loop through each object in the bucket
    for key in bucket.list():
        # Get the object key as a string
        key_str = str(key.key)

        # Split the object key by '/' to get the list of subfolders
        subfolders = key_str.split('/')

        # Filter out subfolders with no name
        subfolders_with_no_name = list(filter(lambda x: x == '', subfolders))

        # If there are subfolders with no name, download the folder locally
        if subfolders_with_no_name:
            # Get the name of the bucket
            bucket_name = bucket.name

            # Create a local directory to store the downloaded folder
            local_dir = './{}'.format(key_str)
            os.makedirs(local_dir, exist_ok=True)

            # Loop through the objects in the folder and download them locally
            for sub_key in bucket.list(prefix=key_str):
                sub_key_str = str(sub_key.key)
                if sub_key_str != key_str:
                    local_file_path = '{}/{}'.format(local_dir, os.path.basename(sub_key_str))
                    try:
                        sub_key.get_contents_to_filename(local_file_path)
                    except IsADirectoryError:
                        pass

            # Print a message indicating that the folder has been downloaded
            print("Folder downloaded: s3://{}/{}".format(bucket_name, key_str))

            # Create an empty folder with no name in the same location as the downloaded folder
            empty_folder_key = key_str + '/'

            # Create a new key in the new cluster with the same path as the downloaded empty name folder
            new_key = new_conn.get_bucket(bucket_name).new_key(empty_folder_key)

            # Upload the empty folder to the new key in the new bucket
            new_key.set_contents_from_string('')

            # Print a message indicating that the empty folder has been uploaded to the new cluster
            print("Empty folder uploaded: s3://{}/{}".format(bucket_name, empty_folder_key))

            # Loop through the files in the downloaded folder and upload them to the new key in the new bucket
            for file_name in os.listdir(local_dir):
                file_path = os.path.join(local_dir, file_name)
                new_file_key = new_conn.get_bucket(bucket_name).new_key(empty_folder_key + file_name)
                new_file_key.set_contents_from_filename(file_path)

            print("File uploaded: s3://{}/{}".format(bucket_name, empty_folder_key + file_name))
            shutil.rmtree(local_dir)
