# Install GoldenDict on Linux

# In Brief

1. download the latest version of DPD [here](https://github.com/digitalpalidictionary/dpd-db/releases/latest)
2. install version 1.5 of GoldenDict
3. in settings, direct GoldenDict to the DPD folder.

Below are detailed *step-by-step* instructions. 

# Detailed Instructions

## Download DPD

First things first, download the latest version of Digital Pāḷi Dictionary from [GitHub](https://github.com/digitalpalidictionary/dpd-db/releases/latest){:target="_blank"}.

## Make a GoldenDict folder

It is recommended to make an easily accessible GoldenDict folder, for example /Documents/GoldenDict

![create new folder](../pics/linux-install/create%20new%20folder.png)

Or in the terminal\
`mkdir /home/your_user_name/Documents/GoldenDict`

(Obviously, substitute your_user_name with your actual user name)

## Unzip

Right-click the DPD zip file in your Downloads folder and open it with Archive Manager.

![archive manager](../pics/linux-install/archive%20manager.png)

Click Extract and select the folder `/Documents/GoldenDict`

![extract](../pics/linux-install/extract.png)

Or in the terminal:

`cd home/your_user_name/Downloads`\
`unzip /home/your_user_name/Downloads/dpd.zip -d /home/your_user_name/Documents/GoldenDict`

## Install GoldenDict

GoldenDict can be installed directly with apt-get:

`sudo apt-get update`\
`sudo apt-get install goldendict`

Or choose the distribution of your choice from [https://pkgs.org/download/goldendict](https://pkgs.org/download/goldendict){:target="_blank"}:

Or directly from the Software Manager:

![software manager](../pics/linux-install/software%20manager.png)

Make sure to install version 1.5, not version 1.0!

## Adding Dictionaries to GoldenDict

Launch the GoldenDict application

Go to Menu > Edit > Dictionaries (Shortcut **F3**)

![dictionaries F3](../pics/linux-install/dictionaries%20F3.png)

Go to Sources > Files.\
Click Add and select folder `/Documents/GoldenDict`

![add](../pics/linux-install/add.png)

Click the recursive tick box √ (this makes sure GoldenDict searches in sub-folders)

![recursive](../pics/linux-install/recursive.png)

Click OK and wait a few moments while the dictionaries are indexing.

You're all setup!

Next learn how to [setup the hotkey](../goldendict/hotkey.md) or [scan popup](../goldendict/scan_popup.md) so you can click on any Pāḷi word in any text and open it immediately in the dictionary.

