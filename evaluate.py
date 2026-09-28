from topography import MyTopo, genDCTraffic
import random
import csv
import numpy as np
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.node import OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

fieldnames = ["traffic_type", "intensity", "iteration", "source", "sink", "mean_completion_time"]


def evaluate(net, traffic_type, traffic_intensity, traffic_generation_time, iterations=10):
    all_hosts = [h.name for h in net.hosts]
    h_src, h_sink = random.sample(all_hosts, 2)
    iter_means = []     # x1, x2, .... x10
    for i in range(iterations):
        completion_times = (genDCTraffic(net, h_src, h_sink, traffic_type, 
                traffic_intensity, traffic_generation_time))
        iter_mean = np.mean(completion_times)    
        iter_means.append(iter_mean)
    return iter_means, h_src, h_sink

def run_experiment(net, output_file = "data.csv", traffic_generation_time = 10):
    with open(output_file, "w") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # Per traffic type
        for traffic_type in (1, 2):
            # Per traffic intensity
            for traffic_intensity in range(1,11, 1):
                # Per traffic generation time
                print(f"Starting {traffic_type}, {traffic_intensity}")
                iter_means, source, sink = evaluate(net, traffic_type, traffic_intensity, 
                                                    traffic_generation_time)        
                for iteration, iteration_mean in zip(range(len(iter_means)), iter_means):
                    writer.writerow({
                        "traffic_type": traffic_type,
                        "intensity": traffic_intensity,
                        "iteration": iteration,
                        "source": source,
                        "sink": sink,
                        "mean_completion_time": iteration_mean,
                    })
                    f.flush()
            

if __name__ == "__main__":
    # Baseline, 20 mbps
    topo = MyTopo(edge_agg_bw=20, agg_core_bw=20, host_bw=20)
    net = Mininet(topo=topo, link=TCLink)
    output_file = "data20mbps.csv"
    net.start()
    run_experiment(net, output_file = output_file)
    net.stop()

    # 80 mbps
    topo = MyTopo(edge_agg_bw=80, agg_core_bw=20, host_bw=20)
    net = Mininet(topo=topo, link=TCLink)
    output_file = "data80mbps.csv"
    net.start()
    run_experiment(net, output_file = output_file)
    net.stop()

    # 160mbps
    topo = MyTopo(edge_agg_bw=20, agg_core_bw=160, host_bw=20)
    net = Mininet(topo=topo, link=TCLink)
    output_file = "data160mbps.csv"
    net.start()
    run_experiment(net, output_file = output_file)
    net.stop()
