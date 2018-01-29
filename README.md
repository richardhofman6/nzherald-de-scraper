# NZ Herald DE Scraper
---
# Introduction
This repo contains a simple Python script I wrote to connect to the NZ Herald Digital Edition site, log in with a subscriber's credentials, and download the daily edition. The only output currently supported is PDF, with each page downloaded as a high resolution PNG and embedded into a PDF.

## Reason for creation
My grandmother recently invested in an iPad, as due to her failing eyesight (macular degeneration... old age sucks!) she was unable to read normal books and newspapers. She doesn't like the normal/free NZ Herald app due to the intrusive advertising and heavily context/touch-based interface, which she finds difficult to use, so she subscribed to and downloaded the NZ Herald Digital Edition app.

Which doesn't work. At all. The first couple of times she used it, it worked, albeit with an unintuitive and slow interface. Then it stopped working entirely. As in, it sits on screen for about 15 seconds, and then simply crashes, without so much as an error. The app was last updated several months ago, and has multiple reviews complaining that it is unusable. I had been waiting for NZ Herald to fix this issue, but evidently it is less than a low priority, so I instead decided to write this script.

The intended use case is that it runs on my home server using my grandmother's NZ Herald credentials, and is executed by a cronjob once daily. The script logs into the NZH DE website, retrieves the metadata for the latest edition of the paper, downloads all the pages (sorted by section) and then generates a PDF output for each. Initially I was intending to simply attach these to an email and send them to her account, however the PDFs are very large (>100MiB in total) so instead I'm intending to write the files under the webroot of an HTTP server, and email her links to each PDF.

This way, the paper is easily zoomable, and viewable through a native, hardware-accelerated PDF viewer built into iOS - a much better experience than an official app that doesn't work at all!

# Usage
At this point, the script has no command line options, so you simply need to edit the configuration file, install the requirements and run it!

#### First, get the sources:
```
$ git clone https://github.com/richardhofman6/nzherald-de-scraper.git
$ cd nzherald-de-scraper
```

#### Then, configure:
```
$ cp config.yml.sample config.yml
$ nano config.yml
```

#### Install dependencies...
```
$ virtualenv nzh_scraper
$ source nzh_scraper/bin/activate
$ pip install -r requirements.txt
```

#### Run the script!
```
$ python nzherald_pdf_generator.py
```

#### (Optional) Set up cronjob.
```
crontab -e
```

You can specify a job along the lines of:

    30 4 * * * /home/yourusername/nzherald-de-scraper/nzh_scraper/bin/python /home/yourusername/nzherald-de-scraper/nzherald_pdf_generator.py

This job will run the command (absolute paths) at the 30th minute of the 4th hour (4:30am). This gives some time for the edition to actually come out and be available, before attempting to scrape it.

# Functionality
## Currently Implemented
These features are implemented and working:

* Authentication with NZHDE website.
* Fetch edition by date.
* Automatically fetch today's edition by default.
* In-memory fetch-to-PDF processing (no temporary files simplifies FS permission/disk space requirements, but you will need >1GB of RAM or swap configured).
* Section-level PDF generation.
* Configurable exclusion of certain section names (e.g. "Home", "Canvas Magazine" - both of which are large sections).

## Planned
* Further configuration options
    * Specify whether to email PDFs or save locally (you'll need a fairly lax SMTP service for these file sizes!)
* HTTP server support:
    * Write files to filesystem.
    * Automatic link URL generation
* Manual use cases (CLI options):
    * Fetch specific edition by date.
    * Fetch specific section(s) only.
    * Save PDFs to specific directory.
    * Output as a sequence of PNGs instead of a PDF.
* Better usability
    * Print metadata and predicted download sizes, etc. only.
    * More informative errors (for example, "edition not available", "incorrect username/password", "section not present", etc.)
