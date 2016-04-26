#-------------------------------------------------------------------------------
# Name:        CADtoParcels
# Purpose:      Convert DWG maps to one cohesive parcel layer
#
# Author:      kristen
#
# Created:     13/10/2015
#-------------------------------------------------------------------------------
def listdirs(folder):
    from os import listdir
    from os.path import isdir, join
    return [d for d in listdir(folder) if isdir(join(folder, d))]

def main():
    #Name: CadtoGeodatabase.py
    # Description: Create a feature dataset
    # Author: ESRI

    # Import system modules
    from arcpy import (env, CreateFileGDB_management, CADToGeodatabase_conversion, Delete_management, FeatureToPolygon_management,
            CopyFeatures_management, MakeFeatureLayer_management, Exists, Append_management)
    from os.path import basename, join

    root = r"G:\pathnamegoeshere\ParcelMosaic" #change path name accordingly

    #create a final file geodatabase
    file_gdb = "FO_ParcelMosaic.gdb" # rename geodatabase to whatever you like
    parcelMosaicName = "FO_Parcels" #rename parcel layer name to whatever you like
    parcelLinesName = "FO_ParcelLines" #rename parcel lines layer name to whatever you like

    #create file geodatabase
    if not Exists(join(root, file_gdb)):
        CreateFileGDB_management(root, file_gdb) #if you run the script multiple times, you'll only need to do this once, so you can comment out the line

    #set up full path name to the final parcel product
    parcelMosaic = join(root, file_gdb, parcelMosaicName)
    parcelLinesMosaic = join(root, file_gdb, parcelLinesName)

    #list township folders underneath the ParcelMosaic folder
    townships = listdirs(root)

    #loop through township folders
    for twp in townships:

        #list map folders underneath the township folder
        maps = listdirs(twp)

        #loop through map folders
        for mapFolder in maps:

            #get the full path to the map folder
            fullPath = join(root, twp, mapFolder)

            # Set workspace
            env.workspace = fullPath

            dwg = mapFolder + ".DWG" # I am guessing that the dwg name is the same as the map folder name, if not, you'll need to tweak this

            # Set local variables
            input_cad_dataset = join(fullPath, dwg)
            out_gdb_path = join(fullPath, dwg[0:-4] + ".gdb")
            out_dataset_name = "conversion"
            reference_scale = "1000"
            spatial_reference = "NAD_1983_StatePlane_Kansas_South_FIPS_1502_Feet"

            # Create a FileGDB for the fds
            CreateFileGDB_management(fullPath, dwg[0:-4] + ".gdb")

            # Execute CreateFeaturedataset
            CADToGeodatabase_conversion(input_cad_dataset, out_gdb_path, out_dataset_name, reference_scale)

            #copy out only parcel ID points
            points = join(out_gdb_path, out_dataset_name, "Point") #set name of existing point layer
            point_wc = "Layer = 'PARCEL_ID'" #create where clause to pull out only PID records
            pointlyr = "pointlyr" #set up name for feature layer conversion
            MakeFeatureLayer_management(points, pointlyr, point_wc) #create feature layer
            parcelID_points = join(out_gdb_path, out_dataset_name, "ParcelID_pt") #create output feature class name
            CopyFeatures_management(pointlyr, parcelID_points) #create feature class of only parcel ID points
            Delete_management(pointlyr) #clean up feature layer

            #separate out different line layer types
            lines = join(out_gdb_path, out_dataset_name, "Polyline")

            #create a list of possible line types
        ##    layerList = ["GOVTICS", "QUARTERSECTION_TICS", "LANDHOOK", "PARCELS", "358", "Butch_ROW", "Centerline", "Church_etc_text", "County Line",
        ##    "CRP", "Landuse", "Quartersections", "railrd", "ROW", "ROWoffset", "section_corners", "section_lines", "SL", "SLP", "Soils", 'Stream', "Zoning"]
        ##    layerList = ["PARCELS", "Landuse", "Soils", "Zoning"]
            layerList = ["PARCELS"]

            #loop through line types
            for lyr in layerList:
                #set up name for feature layer conversion
                linelyr = "linelyr"
                #create where clause to limit attributes retrieved
                wc = "Layer = '" + lyr + "'"

                #add some error trapping in case things crash
                try:
                    #create feature layer
                    MakeFeatureLayer_management(lines, linelyr, wc)
                    #create output feature class name
                    outfc = join(out_gdb_path, out_dataset_name, "Line_" + lyr)
                    #copy over pertinant records
                    CopyFeatures_management(linelyr, outfc)
                except:
                    print "skipping to next layer type"
                finally:
                    #clean up feature layer
                    if Exists(linelyr):
                        Delete_management(linelyr)

            #Convert parcel lines to polygon
            parcelLines = join(out_gdb_path, out_dataset_name, "Line_PARCELS") #input line feature class
            parcelPolys = join(out_gdb_path, out_dataset_name, "Poly_PARCELS") #output polygon feature class

            #make feature layer from parcel ID points to use as the label
            pid_lyr = "pid_lyr"
            MakeFeatureLayer_management(parcelID_points, pid_lyr)

            #http://help.arcgis.com/EN/arcgisdesktop/10.0/help/index.html#//00170000003n000000
            FeatureToPolygon_management(parcelLines, parcelPolys, "", "ATTRIBUTES", pid_lyr)

            print("Converted " + dwg + ". Parcel polygons are in " + parcelPolys)


            #see if the parcel mosaic feature class exists
            if not Exists(parcelMosaic):
                #if not, create a new feature class
                CopyFeatures_management(parcelPolys, parcelMosaic)
            else:
                #if it does exist, append the newly converted parcel polygons
                Append_management(parcelPolys, parcelMosaic, "NO_TEST")

            print("Added " + dwg + " parcel polygons to county mosaic")

            #this section will create a feature class of parcel lines, feel free to comment out if you don't want that
            if not Exists(parcelLinesMosaic):
                CopyFeatures_management(parcelLines, parcelLinesMosaic)
            else:
                Append_management(parcelLines, parcelLinesMosaic, "NO_TEST")

            print("Added " + dwg + " parcel line to county mosaic")



if __name__ == '__main__':
    main()
