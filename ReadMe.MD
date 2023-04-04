# Forsberg Dis Application #
* CURRENT RUNNING TIMES
* Start Up For Cell Tower Locaters
* Around 5 Minutes (ONLY OCCURS ONCE, UPON STARTING APPLICATION)
* Returning Addresses + Pano Images
* 177 LOCATIONS -> Around 4 minutes 

## Using the application ##
* MUST HAVE GOOGLE API KEY 
* GEOCODING API AND STREET VIEW STATIC API MUST BE SELECTED ON GOOGLE DASHBOARD
* API KEY NEEDS INPUTTING IN formatted_address func and pano func 
* Need to first initialise database
* In python console:
* 1.) from app import init_db
* 2.) init_db()

## Walkthrough ## 

### Spatial Indexing Cell-Towers ###
Storing the contents of the cell-towers locations in a spatial index due to the amount of locations as well as this the data structure works very well with geo locations.

### Database ### 
Using sqlite for the database. Stores username, email, csv-file and time the form was completed. Thought necessary so users can look to see if file has already been passed through. Added database clearance option if log file becomes too large.

### Index ###
Home page. Passes all inputs through and validates data. Upon correct data input it calls the formatted_address function.

### Formatted Address ### 
Makes use of the reverse geocoding google api. Takes latitude and longitude from inputted csv file and returns a address. Then returns this output in the form of a csv file inside the ouputs/ file. This func then calls on the pano() func. 

### Pano ### 
Very useful func for gaining context of the location. Makes use of the google static viewer api. Requests 4 different headings of the same location and then stitches the four returned images into one large panoramic image. Passes these images into to_word() which then takes these images and places them into a word document. Pano() also converts the returned results of addresses and pano images into a web page for the user to view.

### To Word ###
Takes the results of the reverse geocoding api as well as the panoramic images and places them into a word file that can either be downloaded or emailed.

### Find_closest_towers ###
* Takes in the co-ordinates of inputted csv file
* Spatial Index of the cell tower locations
* Takes in geopandas dataframe of cell-tower locations
Finds closest cell tower for each location of the inputted csv file

### Cell dist ###
Outputs results of the closest cell-towers to a csv file
Uses folium to plot the locations under two different markers
Red -> Cell Tower
Green -> Inputted File Location
Each of the markers shows the index number of the location.

### Send Email ###
Uses gmail to compose an email to user.
Email address used is the one given in form.
If file is under 25mb then this option is available. 


Attachment is a word document

### Download File ### 
Option is available all the time.
Added as files tend to be over 25mb and thus cannot be emailed.
