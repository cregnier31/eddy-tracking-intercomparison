# from nco import Nco
# from nco.custom import Atted
# nco = Nco()


# nco.ncatted(input="../GLO12_CURR_2023_NA.nc",options=[
#     Atted(
#         mode="overwrite",
#         att_name="units",
#         var_name="vo",
#         value="m/s",
#         stype='c',
#     ),
# ])

# nco.ncatted(input="../GLO12_CURR_2023_NA.nc",options=
#             [Atted(
#         mode="overwrite",
#         att_name="units",
#         var_name="uo",
#         value="m/s",
#         stype='c',
#     ),
# ])


from nco import Nco
from nco.custom import Atted

# Création d'une instance de la classe Nco
nco = Nco()

# Fusion des fichiers avec ncks -A
nco.ncks("../GLO12_CURR_2023_NA.nc","../GLO12_ZOS_2023_NA.nc") 
