import datetime


class DeltaDateComputer:

    @staticmethod
    def compute(startDateString,endDateString):
        startDate = datetime.datetime.strptime(startDateString, "%Y-%m-%d")

        endDate = datetime.datetime.strptime(endDateString,"%Y-%m-%d")
        #endDate提前三天
        endDate -= datetime.timedelta(days=3)

        #获得当天0点时间
        nowDate = datetime.datetime.combine(datetime.date.today(), datetime.time.min)

        T = (endDate - startDate).days
        t = (nowDate - startDate).days

        if t >= T:
            t = T-1

        return (T/252,t/252)

if __name__ == "__main__":
    startDateString = "2016-9-6"
    endDateString = "2016-9-16"
    T,t = DeltaDateComputer.compute(startDateString,endDateString)
    print(T*252)
    print(t*252)