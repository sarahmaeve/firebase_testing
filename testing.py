# connect to google cloud
import errno
import os
import re
import subprocess
import sys

PROJECT_ID = "slandroidtest"
GCLOUD_PATH = "/Users/sarah/gcloud/google-cloud-sdk/bin/gcloud"
GSUTIL_PATH = "/Users/sarah/gcloud/google-cloud-sdk/bin/gsutil"
APK_LOCATION = "/Users/sarah/Downloads/app-debug.apk"
TEST_APK_LOCATION = "/Users/sarah/Downloads/app-debug-androidTest.apk"
LOCAL_OUTPUT_DIR = "./test_output"

def copy_output(target_location):
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
        subprocess.run([GSUTIL_PATH, "cp", gsutil_address, LOCAL_OUTPUT_DIR])
        print("Copying {} ...".format(gsutil_address))
    except subprocess.CalledProcessError:
        print("Failed to copy XML output.")

def output_test_data(run_output):
    """ process output from combined stdout / stderr """
    regex1 = re.compile(b"GCS bucket at \[(.+)\]") # using bytes because of stdout format
    m = re.search(regex1, run_output)
    if m:
        output_location = m[1].decode("utf-8") # get out of bytes
        print("Test Output Located at: {}".format(output_location))
        copy_output(output_location)
    print("Test run complete.")
    return

def cloud_config():
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
    try:
        print("Starting test run.")
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

# sample_output = b'\nHave questions, feedback, or issues? Get support by visiting:\n  https://firebase.google.com/support/\n\nUploading [/Users/sarah/Downloads/app-debug.apk] to Firebase Test Lab...\nUploading [/Users/sarah/Downloads/app-debug-androidTest.apk] to Firebase Test Lab...\nRaw results will be stored in your GCS bucket at [https://console.developers.google.com/storage/browser/test-lab-rur64nxyp1734-jufvw324k5q7s/2020-06-09_13:35:41.276726_nKCX/]\n\nTest [matrix-3ihaxrks9yuk1] has been created in the Google Cloud.\nFirebase Test Lab will execute your instrumentation test on 1 device(s).\nCreating individual test executions...\n................done.\n\nTest results will be streamed to [https://console.firebase.google.com/project/slandroidtest/testlab/histories/bh.9a2d958bfb99c43/matrices/7646598942614275410].\n13:38:01 Test is Pending\n13:38:50 Starting attempt 1.\n13:38:50 Started logcat recording.\n13:38:50 Started crash monitoring.\n13:38:50 Preparing device.\n13:38:50 Logging in to Google account on device.\n13:38:50 Test is Running\n13:39:02 Installing apps.\n13:39:02 Retrieving Pre-Test Package Stats information from the device.\n13:39:02 Retrieving Performance Environment information from the device.\n13:39:02 Started crash detection.\n13:39:02 Started performance monitoring.\n13:39:02 Started video recording.\n13:39:02 Starting instrumentation test.\n13:46:06 Completed instrumentation test.\n13:46:06 Stopped video recording.\n13:46:06 Stopped performance monitoring.\n13:46:06 Stopped crash monitoring.\n13:46:18 Retrieving Post-test Package Stats information from the device.\n13:46:18 Logging out of Google account on device.\n13:46:18 Stopped logcat recording.\n13:46:18 Done. Test time = 419 (secs)\n13:46:18 Starting results processing. Attempt: 1\n13:46:31 Completed results processing. Time taken = 15 (secs)\n13:46:31 Test is Finished\n\nInstrumentation testing complete.\n\nMore details are available at [https://console.firebase.google.com/project/slandroidtest/testlab/histories/bh.9a2d958bfb99c43/matrices/7646598942614275410].\n+---------+------------------------+--------------------------------+\n| OUTCOME |    TEST_AXIS_VALUE     |          TEST_DETAILS          |\n+---------+------------------------+--------------------------------+\n| Failed  | walleye-26-en-portrait | 2 test cases failed, 98 passed |\n+---------+------------------------+--------------------------------+\n'
# output_test_data(sample_output)

cloud_config()
run_tests()

