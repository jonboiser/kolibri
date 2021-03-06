import os
import re

from django.core.urlresolvers import reverse

from kolibri.utils import conf

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin


# valid storage filenames consist of 32-char hex plus a file extension
VALID_STORAGE_FILENAME = re.compile("[0-9a-f]{32}(-data)?\.[0-9a-z]+")

# set of file extensions that should be considered zip files and allow access to internal files
POSSIBLE_ZIPPED_FILE_EXTENSIONS = set([".perseus", ".zip"])
# TODO: add ".epub" and ".epub3" if epub-equivalent of ZipContentView implemented

def get_content_file_name(obj):
    return '{checksum}.{extension}'.format(checksum=obj.id, extension=obj.extension)


# DISK PATHS

def get_content_dir_path(datafolder=None):
    return os.path.join(
        datafolder,
        "content",
    ) if datafolder else conf.OPTIONS["Paths"]["CONTENT_DIR"]

def get_content_database_dir_path(datafolder=None):
    """
    Returns the path to the content sqlite databases
    ($HOME/.kolibri/content/databases on POSIX systems, by default)
    """
    path = os.path.join(
        get_content_dir_path(datafolder),
        "databases",
    )
    if not os.path.isdir(path):
        try:
            os.makedirs(path)
        # When importing from USB, it does not need to create a database
        # directory under the external drives that are not writable.
        except OSError:
            pass
    return path

def get_content_database_file_path(channel_id, datafolder=None):
    """
    Given a channel_id, returns the path to the sqlite3 file
    ($HOME/.kolibri/content/databases/<channel_id>.sqlite3 on POSIX systems, by default)
    """
    return os.path.join(
        get_content_database_dir_path(datafolder),
        "{}.sqlite3".format(channel_id),
    )

def get_content_storage_dir_path(datafolder=None):
    path = os.path.join(
        get_content_dir_path(datafolder),
        "storage",
    )
    if not os.path.isdir(path):
        os.makedirs(path)
    return path

def get_content_storage_file_path(filename, datafolder=None):
    assert VALID_STORAGE_FILENAME.match(filename), "'{}' is not a valid content storage filename".format(filename)
    return os.path.join(
        get_content_storage_dir_path(datafolder),
        filename[0],
        filename[1],
        filename,
    )


# URL PATHS

def get_content_url(baseurl=None):
    return urljoin(
        baseurl or conf.OPTIONS['Urls']['CENTRAL_CONTENT_BASE_URL'],
        "content/",
    )

def get_content_database_url(baseurl=None):
    return urljoin(
        get_content_url(baseurl),
        "databases/",
    )

def get_content_database_file_url(channel_id, baseurl=None):
    return urljoin(
        get_content_database_url(baseurl),
        "{}.sqlite3".format(channel_id),
    )

def get_content_storage_url(baseurl=None):
    return urljoin(
        get_content_url(baseurl),
        "storage/",
    )

def get_content_storage_remote_url(filename, baseurl=None):
    return "{}{}/{}/{}".format(get_content_storage_url(baseurl), filename[0], filename[1], filename)

def get_channel_lookup_url(identifier=None, baseurl=None):
    studio_url = "/api/public/v1/channels"
    if identifier:
        studio_url += "/lookup/{}".format(identifier)
    return urljoin(
        baseurl or conf.OPTIONS['Urls']['CENTRAL_CONTENT_BASE_URL'],
        studio_url
    )

def get_content_storage_file_url(filename, baseurl=None):
    """
    Return the URL at which the specified file can be accessed. For regular files, this is a link to the static
    file itself, under "/content/storage/". For "zip" files, this points to a dynamically generated view that
    allows the client-side to index into the files within the zip.
    """
    ext = os.path.splitext(filename)[1]
    if ext in POSSIBLE_ZIPPED_FILE_EXTENSIONS:
        return reverse("zipcontent", kwargs={"zipped_filename": filename, "embedded_filepath": ""})
    else:
        return "{}{}/{}/{}".format(get_content_storage_url(baseurl), filename[0], filename[1], filename)
