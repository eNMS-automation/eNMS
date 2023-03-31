## Overview 

The Files management provides information about a specific folder (local or network)
and provides a mechanism to interact with files and folders in that location.

A routine file watcher will detect and add new files and folders as they are created,
and it will also update their modified date when they change.  It will also mark files 
and folders as Deleted if they are removed.   A manual "Scan Folder" option also 
provides a way to reload the file and folder data in a specific folder.

The Files information can be viewed either from:

- The System -> Files navigation menu, or 

  ![Files - Tables](../_static/system/files_table1.PNG)

- From the top navigation bar, from the Files icon.

  ![Files - Files window](../_static/system/files_window1.PNG)


## Folder Navigation  

Opening a specific folder will show the Files and Folders contained inside.

Click on the any Folder to open it and view the Files (and Folders) that it contains.
The top of the page will display the Current Folder.

To navigate between folders: 

- Click on any of the blue breadcrumbs highlighted next to the `Current Folder` label, or 
- Click on the "up" `^` navigation button at the top, or 
- Click on any folder shown inside the table itself.

![Files - Folder Navigation](../_static/system/files_folder_navigation.png)

## Files Management 

These actions from the top button bar provide ways to create folders, create files, and 
delete both folders and files from the database. 

![Files - Folder Navigation](../_static/system/file_top_button_bar.png)

- `Create New Folder` - create a new folder in the current folder

  ![Files - Folder Navigation](../_static/system/file_new_folder.png)

- `Upload Files` - upload one or more files into the current folder 

  - To start the upload: 

    ![Files - Files window](../_static/system/file_upload1.png)

  - When finished, the window will show successful checkmark(s): 

    ![Files - Files window](../_static/system/file_upload2.png)

- `Scan Folder` - manually refresh the contents based on what is physically present in the folder location

  ![Files - Files window](../_static/system/file_scan_folder.png)

- `Bulk Deletion` - delete all the displayed files/folders from the database only

  ![Files - Folder Navigation](../_static/system/files_bulk_delete.PNG)

!!! Note

	Today the Delete button does not physically remove files - for safety reasons.
	Unless removed from the underlying location(s), a Scan Folder will restore 
	them in this view.
  
These actions apply to each individual file or folder:

- `Copy Path to Clipboard` - copy the absolute path to the file or folder to the clipboard
- `Download File` - downloads a single file or a .TGZ file with contents of the entire folder 
- `Upload Files in Folder` - only shown for a Folder, opens the Upload File window
- `Edit` - edit the File or Folder details (e.g., Description)
- `File Content` - only shown for a File, show the File - with option to save changes
- `Delete` - remove file/folder from the database (not the file system)

 
