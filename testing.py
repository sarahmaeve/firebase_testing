"""Automate Firebase Android Tests"""
import errno
import os
import re
import subprocess
import sys

# Replace with the locations of your binaries and command paths
# PROJECT_ID = ""  # firebase project you've made in advance
# GCLOUD_PATH = "" # which gcloud
# GSUTIL_PATH = "" # which gsutil
# APK_LOCATION = "" # where your binary is
# TEST_APK_LOCATION = "" # where your tests are
# example locations for my run:
PROJECT_ID = "slandroidtest"
GCLOUD_PATH = "/Users/sarah/gcloud/google-cloud-sdk/bin/gcloud"
GSUTIL_PATH = "/Users/sarah/gcloud/google-cloud-sdk/bin/gsutil"
APK_LOCATION = "/Users/sarah/Downloads/app-debug.apk"
TEST_APK_LOCATION = "/Users/sarah/Downloads/app-debug-androidTest.apk"
LOCAL_OUTPUT_DIR = "./test_output"

def copy_output(target_location):
    """Copy XML output from gcloud to local directory"""
    # create location if it doesn't exist
    # standard incantation
    try:
        os.makedirs(LOCAL_OUTPUT_DIR)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    # get gsutil address
    subaddr = "/".join(target_location.split('/')[-3:])
    gsutil_address = "gs://{}**.xml".format(subaddr)

    try:
        subprocess.run([GSUTIL_PATH, "cp", gsutil_address, LOCAL_OUTPUT_DIR], check=True)
        print("Copying {} to {}".format(gsutil_address, LOCAL_OUTPUT_DIR))
    except subprocess.CalledProcessError:
        print("Failed to copy XML output.")

def output_test_data(run_output):
    """ process output from combined stdout / stderr """
    regex1 = re.compile(b"GCS bucket at \[(.+)\]") # using bytes because of stdout format
    m = re.search(regex1, run_output)
    if m is not None:
        output_location = m[1].decode("utf-8") # get out of bytes
        print("Full test output Located at: {}".format(output_location))
        copy_output(output_location)

    # print the pretty text box with test output from STDOUT
    regex2 = re.compile(b"\n(\+--.*$)", re.DOTALL)
    box_match = re.search(regex2, run_output)
    if box_match is not None:
        print(box_match[1].decode("utf-8"))

    print("Test run complete.")

def cloud_config():
    """connect to your firebase project"""
    try:
        output = subprocess.run([GCLOUD_PATH, "config", "set", "project", PROJECT_ID],
                                check=True, capture_output=True)
        if "WARNING" in str(output.stderr):
            print("PROJECT_ID {} incorrect? Exiting.".format(PROJECT_ID))
            sys.exit(1)
        print("Updated configuration to {}.".format(PROJECT_ID))
    except subprocess.CalledProcessError:
        print("Configuration Error: gcloud config command incorrect?")

def run_tests():
    """execute all tests then output data"""
    try:
        print("Starting test run.")
        # could add the following : a set of subtests. However in this case, 100 / 100
        output = subprocess.run([GCLOUD_PATH, "firebase", "test", "android", "run",
                                 "--type", "instrumentation",
                                 "--app", APK_LOCATION,
                                 "--test", TEST_APK_LOCATION,
                                 "--use-orchestrator"],  # app failures without this in several runs
                                check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print("All tests passed.")
        output_test_data(output.stdout)

    except subprocess.CalledProcessError as e:
        print("Some tests failed.")
        output_test_data(e.stdout)

cloud_config()
run_tests()
