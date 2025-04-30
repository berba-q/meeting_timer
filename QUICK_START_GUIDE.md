# JW Meeting Timer - Quick Start Guide

This guide covers the new features added in the latest version of the JW Meeting Timer application.

## New Features Overview

1. **Meeting Templates**
2. **Manual Meeting Creation**
3. **Meeting Editor**
4. **Flexible Meeting Source Options**
5. **Timer Testing Improvements**

## Setting Up Meeting Sources

### Configuring Meeting Source Mode

1. Open **File → Settings**
2. Select the **Meeting Source** tab
3. Choose your preferred method for creating meetings:
   - **Web Scraping**: Automatically download from wol.jw.org (original method)
   - **Template-Based**: Use templates with customizations
   - **Manual Entry**: Create meetings from scratch

![Meeting Source Settings](screenshots/meeting_source_settings.png)

### Additional Options

- **Automatically update meetings from the web**: Enable to fetch meetings on startup
- **Save scraped meetings as templates**: Save web-scraped meetings as templates
- **Always manually enter weekend songs**: Forces manual song entry for weekend meetings

## Creating and Editing Meetings

### Creating a New Meeting

1. Click **File → New Meeting**
2. Enter meeting details (title, date, time)
3. Select a template from the dropdown
4. Click **Load Template** to populate the structure
5. Add/Edit sections and parts as needed
6. Click **Save** when complete

![Meeting Editor](screenshots/meeting_editor.png)

### Adding Sections and Parts

1. In the meeting editor, click **Add Section**
2. Enter a name for the section (e.g., "TREASURES FROM GOD'S WORD")
3. With the section selected, click **Add Part**
4. Enter part details:
   - Title (e.g., "Bible Reading")
   - Duration in minutes
   - Presenter name (optional)
5. Repeat for all meeting parts

### Editing the Current Meeting

1. Select a meeting from the dropdown in the main window
2. Click **File → Edit Current Meeting**
3. Make your changes
4. Click **Save** to update the meeting

## Using Templates

### Saving a Meeting as Template

1. Create or edit a meeting with your desired structure
2. Click **Save as Template** in the meeting editor
3. The template will be saved based on meeting type (Midweek/Weekend)

### Creating a Meeting from a Template

1. Open the meeting editor (**File → New Meeting**)
2. Select the meeting type
3. Choose a template from the dropdown menu
4. Click **Load Template**
5. Customize as needed
6. Click **Save**

## Updating Meetings

### Web Scraping Mode

When using web scraping mode, click the **Update Meetings from Web** button (F5) to fetch the latest meetings from wol.jw.org.

### Template/Manual Mode

When using template or manual mode, clicking the update button will show additional options:

![Update Options](screenshots/update_options.png)

- **Update from Web**: Force a web update regardless of current mode
- **Edit Current Meeting**: Open the editor for the current meeting
- **Create New Meeting**: Open the editor to create a new meeting

## Tips for Success

1. **Use templates for consistent meetings**: Save your common meeting formats as templates to save time.
2. **Weekend songs**: Check "Always manually enter weekend songs" to leave song placeholders in weekend meetings.
3. **Meeting updates**: Consider using "Save scraped meetings as templates" to maintain custom structures while getting the latest meeting content.
4. **Edit while running**: You can edit a meeting even after it has started by using File → Edit Current Meeting.

## Need Help?

If you encounter any issues or have questions about the new features, please refer to the full documentation or contact support.

Happy timing!