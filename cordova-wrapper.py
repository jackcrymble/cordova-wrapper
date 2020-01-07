import argparse
import os
import subprocess
import sys

def _run_command(command_str):
    output = subprocess.run(args=command_str.split())
    if output.returncode != 0:
        print('ERROR: %s FAILED...' % command_str)
        sys.exit('Quitting...')

def _setupArgs(parser):
    parser.add_argument('-p', help="Path for cordova project. Used for name and id also", required=True)
    parser.add_argument('--clean', help="Clean build. Will delete any existing cordova projects with same name", required=False, action='store_true')
    parser.add_argument('--rename', help="Change display name for project. You will be prompted to enter a new display name for the project", required=False, action='store_true')
    parser.add_argument('--rebuild-only', help="Rebuild changes on existing cordova project", action="store_true")
    parser.add_argument('-f', help="Plugin file path (default none)", default=None, required=False)
    return parser.parse_args()

def _updateFile(path, old_str, new_str):
    # Open existing index file
    with open(path, 'r') as file :
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace(old_str, new_str)

    # Write the file out again
    with open(path, 'w') as file:
        file.write(filedata)

def _updateConfigXML(path, name, display_name):
    old_str = '<name>%s</name>' % name
    new_str = '<name>%s</name>' % display_name
    _updateFile(path, old_str, new_str)

def _updateIndexHTML(path):
    old_str = '</head>'
    new_str = '<script type="text/javascript" src="cordova.js"></script>\n</head>'
    _updateFile(path, old_str, new_str)

def prepare_workspace(clean, path, rename):
    if not os.path.exists('package.json'):
        sys.exit('package.json not found. Cordova Wrapper must be run within an angular project')

    if clean:
        if not input('Are you sure you want to delete cordova project: %s (y/N): ' % path).lower() == 'y':
            sys.exit('Quitting...')
        if os.path.exists('../%s' % path):
            command = 'rm -rf ../%s' % path
            subprocess.run(args=command.split())
        else:
            print('Project does not already exist. Continuing...')

    display_name = input('Enter display name for app: ') if rename else APP_NAME

    return display_name

def create(name, id, path, display_name):

    # Move up to full project directory
    os.chdir('..')

    # Create the empty cordova project
    _run_command('cordova create %s %s %s' % (path, id, name))

    # Enter Cordova Project
    os.chdir(path)

    # Add Android platform
    command = 'cordova platform add android'
    subprocess.run(args=command.split())

    # Update Config file to include icon to display
    _updateConfigXML('config.xml', name, display_name)

    # Return to starting directory
    os.chdir('../application')

def plugins(path, file_path):
    # Enter Cordova Project
    os.chdir('../%s' % path)

    if file_path is not None:
        with open(os.getcwd() + '/' + args.f, 'r') as f:
            for line in f:
                command = 'cordova plugin add %s' % line[:2]
                print('DUMMY:: ', command)

    # Return to starting directory
    os.chdir('../application')

def build(path, angular_project_name):
    command = 'ng build --configuration=production --prod --aot --base-href ./'
    subprocess.run(args=command.split())

    # Cannot find files with subprocess run, so using subprocess call with shell instead
    command = 'cp -r dist/%s/* ../%s/www/' % (angular_project_name, path)
    subprocess.call(command, shell=True)

    _updateIndexHTML('../%s/www/index.html' % path)

    # Enter Cordova Project
    os.chdir('../%s' % path)

    command = 'cordova build'
    subprocess.run(args=command.split())

    # Return to starting directory
    os.chdir('../application')

def clean_up(path):
    # Create directory for apk
    directory = '../apks'
    if not os.path.exists(directory):
        os.mkdir(directory)

    # Move apk to new directory
    command = 'cp ../%s/platforms/android/app/build/outputs/apk/debug/app-debug.apk ../apks/' % path
    subprocess.run(args=command.split())

    print('To install apk, connect phone and run following command...')
    print('adb install -r ../apks/app-debug.apk')

###########################
# Executed Code Below
###########################

parser = argparse.ArgumentParser(description=
    """
    Cordova Wrapper script
    """
)
args = _setupArgs(parser)

APP_PATH         = args.p + '-cordova'
APP_ID           = 'com.crymbledev.' + args.p
APP_NAME         = args.p.lower()
PLUGIN_FILE_PATH = args.f
ANGULAR_PROJECT  = os.getcwd().split('/')[-2]
CLEAN_PROJECT    = args.clean
RENAME_PROJECT   = args.rename
REBUILD_PROJECT  = args.rebuild_only

# Skip if only rebuilding
if not REBUILD_PROJECT:
    # Prep workspace
    new_display_name = prepare_workspace(CLEAN_PROJECT, APP_PATH, RENAME_PROJECT)

    # Create the app
    create(APP_NAME, APP_ID, APP_PATH, new_display_name)

    # Add plugins
    plugins(APP_PATH, PLUGIN_FILE_PATH)

# Build angular project and insert to cordova project
build(APP_PATH, ANGULAR_PROJECT)

# Move apk file to easily accessible location
clean_up(APP_PATH)
