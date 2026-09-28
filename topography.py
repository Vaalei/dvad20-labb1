#!/usr/bin/env python3
import time
import threading
import numpy as np
import os

from scapy.all import PcapReader, TCP, IP
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.node import OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

# --- ECDF-punkter (fyll på med dina avlästa värden) ---
web_search_x = [0, 10000, 20000, 30000, 50000, 80000, 100000]
web_search_y = [0.0, 0.15, 0.30, 0.60, 0.90, 0.95, 1.00]

data_mining_x = [180, 300, 450, 570, 590, 650, 710, 820, 920]
data_mining_y = [0.10, 0.20, 0.30, 0.40, 0.60, 0.70, 0.80, 0.90, 1.00]

def analyze_pcap(pcap_path, server_port=5001):
    flows = {}
    
    with PcapReader(pcap_path) as pcap_reader:
        for pkt in pcap_reader:
            if TCP in pkt:
                tcp_layer = pkt[TCP]
                ts = float(pkt.time)
                
                if tcp_layer.dport == server_port:
                    src_port = tcp_layer.sport
                    if src_port not in flows:
                        flows[src_port] = {"start": ts, "end": ts}
                    else:
                        flows[src_port]["end"] = ts
                elif tcp_layer.sport == server_port:
                    dst_port = tcp_layer.dport
                    if dst_port in flows:
                        flows[dst_port]["end"] = max(flows[dst_port]["end"], ts)
    
    return [data["end"] - data["start"] for data in flows.values()]

def getSampleFromEcdf(x_points, y_points, size=1):
    u = np.random.uniform(0, 1, size=size)
    samples = np.interp(u, y_points, x_points)
    return samples[0] if size == 1 else samples

def get_samples(traffic_type):
    if traffic_type == 1:
        return getSampleFromEcdf(web_search_x, web_search_y)
    elif traffic_type == 2:
        return getSampleFromEcdf(data_mining_x, data_mining_y)
    else:    
        print("Traffic type has to be 1 (Web search) or 2 (Data-mining)")
        return None

def genDCTraffic(net, traffic_source, traffic_sink, traffic_type,
                  traffic_intensity, traffic_generation_time):
    h_src = net.get(traffic_source)
    h_sink = net.get(traffic_sink)
    sink_ip = h_sink.IP()
    intf_name = h_sink.intf().name

    h_src.cmd("pkill -9 -f iperf")
    h_sink.cmd("pkill -9 -f iperf")
    h_sink.cmd("pkill -9 -f tcpdump")
    time.sleep(0.2)

    h_sink.cmd("iperf -s &")
    time.sleep(0.5)

    pcap_file = f"/tmp/capture_{traffic_type}_{traffic_intensity}.pcap"
    h_sink.cmd(f"tcpdump -i {intf_name} -w {pcap_file} &")
    time.sleep(1)

    gen_start = time.monotonic()

    while time.monotonic() - gen_start < traffic_generation_time:
        loop_start = time.monotonic()

        for _ in range(traffic_intensity):
            flow_size = int(get_samples(traffic_type))
            h_src.cmd(f"iperf -c {sink_ip} -n {flow_size} &")

        elapsed = time.monotonic() - loop_start
        time.sleep(max(0, 1 - elapsed))

    # Await all iperf processes
    while True:
        remaining = h_src.cmd("pgrep -f 'iperf -c'").strip()
        if not remaining:
            break
        time.sleep(0.2)

    h_src.cmd("pkill -f 'iperf -c'")
    h_sink.cmd("pkill -f 'iperf -s'")
    time.sleep(0.5)
    h_sink.cmd("pkill -f tcpdump")
    
    completion_times = analyze_pcap(pcap_file)
    os.remove(pcap_file)
    return completion_times


class MyTopo(Topo):
    def build(self, edge_agg_bw=20, agg_core_bw=20, host_bw=20, delay="1ms"):
        root = self.addSwitch("s0")
        for i in range(4):
            switch = self.addSwitch(f"s{i+1}")
            self.addLink(root, switch, bw=agg_core_bw, delay=delay)       
            for j in range(2):
                switch2 = self.addSwitch(f"s{i+1}-{j+1}")
                self.addLink(switch, switch2, bw=edge_agg_bw, delay=delay)  
                for k in range(2):
                    host = self.addHost(f"h{i+1}-{j+1}-{k+1}")
                    self.addLink(switch2, host, bw=host_bw, delay=delay)   


topos = {'main': (lambda: MyTopo())}


if __name__ == "__main__":
    setLogLevel("info")
    topo = MyTopo()
    net = Mininet(topo=topo, link=TCLink, switch=OVSSwitch)
    net.start()

    # Exempel: generera trafik mellan två hostar i 10 sekunder
    genDCTraffic(net, "h1-1-1", "h2-1-1", traffic_type=1,
                 traffic_intensity=2, traffic_generation_time=10)

    CLI(net)
    net.stop()
