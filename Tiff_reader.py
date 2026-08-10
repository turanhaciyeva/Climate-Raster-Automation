# -*- coding: utf-8 -*-

import arcpy
import os
import re
import traceback

arcpy.env.overwriteOutput = True

# ---------------------------------------------------------
# PARAMETERS
# ---------------------------------------------------------

rayon_fc = arcpy.GetParameterAsText(0)
rayon_field = arcpy.GetParameterAsText(1)
tif_folder = arcpy.GetParameterAsText(2)
output_excel = arcpy.GetParameterAsText(3)

# ---------------------------------------------------------
# MONTH NAMES
# ---------------------------------------------------------

month_names = {
    1: u"Yanvar",
    2: u"Fevral",
    3: u"Mart",
    4: u"Aprel",
    5: u"May",
    6: u"Iyun",
    7: u"Iyul",
    8: u"Avqust",
    9: u"Sentyabr",
    10: u"Oktyabr",
    11: u"Noyabr",
    12: u"Dekabr"
}

# ---------------------------------------------------------
# CHECK SPATIAL ANALYST
# ---------------------------------------------------------

try:
    arcpy.CheckOutExtension("Spatial")
except:
    arcpy.AddError("Spatial Analyst extension aktiv deyil.")
    raise

try:

    # -----------------------------------------------------
    # TEMP FOLDER / GDB
    # -----------------------------------------------------

    temp_folder = os.path.join(
        arcpy.env.scratchFolder,
        "Climate_Rayon_Temp"
    )

    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    temp_gdb = os.path.join(temp_folder, "temp.gdb")

    if not arcpy.Exists(temp_gdb):
        arcpy.CreateFileGDB_management(
            temp_folder,
            "temp.gdb"
        )

    arcpy.AddMessage("--------------------------------------")
    arcpy.AddMessage("Climate Raster Analysis")
    arcpy.AddMessage("--------------------------------------")

    # -----------------------------------------------------
    # FIND TIF FILES
    #
    # Examples:
    # wc2.1_2.5m_tmax_2019-01.tif
    # wc2.1_2.5m_tmin_2019-01.tif
    # wc2.1_2.5m_prec_2019-01.tif
    # -----------------------------------------------------

    tif_files = []

    for f in os.listdir(tif_folder):

        if not f.lower().endswith(".tif"):
            continue

        match = re.search(
            r"_(tmax|tmin|prec)_(\d{4})-(\d{2})\.tif$",
            f,
            re.IGNORECASE
        )

        if match:

            variable = match.group(1).lower()
            year = int(match.group(2))
            month = int(match.group(3))

            tif_files.append(
                (
                    f,
                    variable,
                    year,
                    month
                )
            )

    if len(tif_files) == 0:
        arcpy.AddError(
            "Qovluqda uygun TIF tapilmadi."
        )
        raise Exception("TIF tapilmadi")

    tif_files.sort(
        key=lambda x: (
            x[2],
            x[3],
            x[1]
        )
    )

    arcpy.AddMessage(
        "Tapilan TIF sayi: {0}".format(
            len(tif_files)
        )
    )

    # -----------------------------------------------------
    # RESULT DICTIONARY
    #
    # (rayon, year, month):
    # {
    #     "tmax": value,
    #     "tmin": value,
    #     "prec": value
    # }
    # -----------------------------------------------------

    results = {}

    # -----------------------------------------------------
    # PROCESS EACH RASTER
    # -----------------------------------------------------

    total = len(tif_files)

    for i, item in enumerate(tif_files):

        filename, variable, year, month = item

        raster = os.path.join(
            tif_folder,
            filename
        )

        arcpy.AddMessage("")

        arcpy.AddMessage(
            "[{0}/{1}] {2}".format(
                i + 1,
                total,
                filename
            )
        )

        out_table = os.path.join(
            temp_gdb,
            "zs_{0}_{1}_{2}".format(
                variable,
                year,
                str(month).zfill(2)
            )
        )

        if arcpy.Exists(out_table):
            arcpy.Delete_management(out_table)

        # -------------------------------------------------
        # ZONAL STATISTICS
        # Rayon daxilinde orta raster deyeri
        # -------------------------------------------------

        arcpy.sa.ZonalStatisticsAsTable(
            rayon_fc,
            rayon_field,
            raster,
            out_table,
            "DATA",
            "MEAN"
        )

        # -------------------------------------------------
        # READ RESULTS
        # -------------------------------------------------

        with arcpy.da.SearchCursor(
            out_table,
            [
                rayon_field,
                "MEAN"
            ]
        ) as cursor:

            for row in cursor:

                rayon = row[0]
                value = row[1]

                key = (
                    rayon,
                    year,
                    month
                )

                if key not in results:

                    results[key] = {
                        "tmax": None,
                        "tmin": None,
                        "prec": None
                    }

                results[key][variable] = value

    # -----------------------------------------------------
    # CREATE FINAL TABLE
    # -----------------------------------------------------

    final_table = os.path.join(
        temp_gdb,
        "Climate_Rayon_Result"
    )

    if arcpy.Exists(final_table):
        arcpy.Delete_management(
            final_table
        )

    arcpy.CreateTable_management(
        temp_gdb,
        "Climate_Rayon_Result"
    )

    arcpy.AddField_management(
        final_table,
        "RAYON",
        "TEXT",
        field_length=100
    )

    arcpy.AddField_management(
        final_table,
        "YEAR",
        "LONG"
    )

    arcpy.AddField_management(
        final_table,
        "MONTH",
        "TEXT",
        field_length=20
    )

    # Tam eded olmasi ucun LONG
    arcpy.AddField_management(
        final_table,
        "TMAX",
        "LONG"
    )

    arcpy.AddField_management(
        final_table,
        "TMIN",
        "LONG"
    )

    arcpy.AddField_management(
        final_table,
        "PREC",
        "LONG"
    )

    # -----------------------------------------------------
    # SORT RESULTS
    # -----------------------------------------------------

    sorted_keys = sorted(
        results.keys(),
        key=lambda x: (
            unicode(x[0]),
            x[1],
            x[2]
        )
    )

    # -----------------------------------------------------
    # INSERT RESULTS
    # -----------------------------------------------------

    with arcpy.da.InsertCursor(
        final_table,
        [
            "RAYON",
            "YEAR",
            "MONTH",
            "TMAX",
            "TMIN",
            "PREC"
        ]
    ) as cursor:

        for key in sorted_keys:

            rayon, year, month = key

            tmax = results[key]["tmax"]
            tmin = results[key]["tmin"]
            prec = results[key]["prec"]

            # ---------------------------------------------
            # ROUND TO INTEGER
            # ---------------------------------------------

            if tmax is not None:
                tmax = int(round(tmax))

            if tmin is not None:
                tmin = int(round(tmin))

            if prec is not None:
                prec = int(round(prec))

            cursor.insertRow(
                [
                    rayon,
                    year,
                    month_names[month],
                    tmax,
                    tmin,
                    prec
                ]
            )

    # -----------------------------------------------------
    # EXPORT TO EXCEL
    # ArcMap 10.8 -> .xls
    # -----------------------------------------------------

    root, ext = os.path.splitext(
        output_excel
    )

    if ext.lower() != ".xls":
        output_excel = root + ".xls"

    arcpy.AddMessage("")
    arcpy.AddMessage("Excel yaradilir...")

    arcpy.TableToExcel_conversion(
        final_table,
        output_excel,
        "NAME",
        "CODE"
    )

    # -----------------------------------------------------
    # FINISH
    # -----------------------------------------------------

    arcpy.AddMessage("")
    arcpy.AddMessage("--------------------------------------")
    arcpy.AddMessage("HAZIRDIR")
    arcpy.AddMessage("--------------------------------------")
    arcpy.AddMessage("Excel fayli yaradildi.")

except Exception as e:

    arcpy.AddError("")
    arcpy.AddError("XETA BAS VERDI:")
    arcpy.AddError(str(e))
    arcpy.AddError(
        traceback.format_exc()
    )

finally:

    try:
        arcpy.CheckInExtension(
            "Spatial"
        )
    except:
        pass