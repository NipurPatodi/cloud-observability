
def get_avg_time(file):
    with open(f'/Users/npatodi/code/ray-obs/cloud-observability/serve/stressTest/rsrc/{file}') as f:
        ctr = 0
        sum = 0.0
        for line in f:
            tkn = line.rstrip().split("- Metric exposer time with optimization = ")
            if len(tkn)>1:
                sum += float(tkn[1])
                ctr+=1
        #print ((sum/ctr)*1000)
        print("{:.6f}".format((sum/ctr)*1000))


def get_avg_time_un(file):
    with open(f'/Users/npatodi/code/ray-obs/cloud-observability/serve/stressTest/rsrc/{file}') as f:
        ctr = 0
        sum = 0.0
        for line in f:
            try:
                tkn = line.rstrip().split("- Metric exposer time with no optimization = ")
                if len(tkn)>1:
                    sum += float(tkn[1])*-1
                    ctr+=1
            except Exception as e:
                print (e)
        #print ((sum/ctr)*1000)
        print("{:.6f}".format((sum/ctr)*1000))

get_avg_time("50_10/50_10.log")
get_avg_time("100_10/100_10.log")
get_avg_time("150_10/150_10.log")

get_avg_time_un("50_10/50_10_uo.log")
get_avg_time_un("100_10/100_10_uo.log")
get_avg_time_un("150_10/150_10_uo.log")