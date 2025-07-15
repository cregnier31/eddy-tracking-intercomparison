# =======================================
# Namelist for model & obs eddy detection
# =======================================
# Parameters for detection
WAVELENGTH  = 500
ORDER_FILTER= 1
SHAPE_ERROR = 55
PIXEL_MIN   = 5
PIXEL_MAX   = 2000
AMP_MIN     = 0.002
# Variable name (ssh, ssu, ssv) depending on considered obs & model
# data_mod_dict = { model_acro : [ ssu_mod_name, 
#                                  ssv_mod_name, 
#                                  ssh_mod_name
#                                ] }
#data_mod_dict = dict()
# NRT datasets (from MDS but also other model data
# NB.: ARC not available in regular mercator grid, only on stereographic grid ==> ARC removed from the MFC choice
data_mod_dict_NRT = { "GLO" : [ "uo", 
                                "vo", 
                                "zos"
                              ],
                      "IBI" : [ "uo", 
                                "vo", 
                                "zos"
                              ],
                      "MED" : [ "uo", 
                                "vo", 
                                "zos" 
                              ],
                      "NWS" : [ "uo", 
                                "vo", 
                                "zos" 
                              ],
                      "BAL" : [ "uo", 
                                "vo", 
                                "zos_detided" 
                              ],
                      "BLK" : [ "uo", 
                                "vo", 
                                "zos" 
                              ] }
#
# MFC MY datasets !!! not interim ==> delayed mode from 1993 !!!
# NB. ssh for BAL isn't available, only sla ==> BAL is remove from this choice for MY datasets
data_mod_dict_MY = { "GLO" : [ "uo", 
                               "vo", 
                               "zos" 
                             ],
                     "IBI" : [ "uo", 
                               "vo", 
                               "zos"
                             ],
                     "MED" : [ "uo", 
                               "vo", 
                               "zos"
                             ],
                     "NWS" : [ "uo", 
                               "vo", 
                               "zos"
                             ],
                     "BLK" : [ "uo", 
                               "vo", 
                               "zos"
                             ],
                  "ORCA36" : [ "uos", 
                               "vos", 
                               "sossheig"
                             ] }
#
# Obs data 
#   - NRT
data_obs_dict_NRT = { "AVISO" : [ "ugos", 
                                  "vgos", 
                                  "adt" 
                               ],
                      "AVISO-EU" : [ "ugos", 
                                     "vgos", 
                                     "adt" 
                               ] }
#   - MY
data_obs_dict_MY = { "AVISO" : [ "ugos", 
                                 "vgos", 
                                 "adt" 
                               ],
                     "AVISO-EU" : [ "ugos", 
                                    "vgos", 
                                    "adt" 
                               ] }
