conda env create -f ../env.yaml -y 

copernicusmarine login


copernicusmarine subset --dataset-id cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m --force-dataset-version 202211 --variable uo --variable vo --start-datetime 2023-01-01T00:00:00 --end-datetime 2023-12-29T00:00:00 --minimum-longitude -70 --maximum-longitude 10 --minimum-latitude 10 --maximum-latitude 60 --minimum-depth 0.49402499198913574 --maximum-depth 0.49402499198913574 --output-filename GLO12_CURR_2023_NA.nc

copernicusmarine subset --dataset-id cmems_mod_glo_phy_anfc_0.083deg_P1D-m --force-dataset-version 202211 --variable zos --start-datetime 2023-01-01T00:00:00 --end-datetime 2023-12-31T00:00:00 --minimum-longitude -70 --maximum-longitude 10 --minimum-latitude 10 --maximum-latitude 60 --minimum-depth 0.49402499198913574 --maximum-depth 0.49402499198913574 --output-filename GLO12_ZOS_2023_NA.nc
