import datetime as dt
#
# Class definition
# ----------------
class CnesJulianCal(object):
        datefmt = "%Y%m%d"
        cnes_origin = dt.date(1950,1,1).toordinal()
        def fromjulian(self, p_julian):
                return dt.date.fromordinal(p_julian + self.cnes_origin).strftime(self.datefmt)
        def tojulian(self, p_date):
                o_date = dt.datetime.strptime(p_date, self.datefmt)
                return o_date.toordinal() - self.cnes_origin
#
# --------------------
