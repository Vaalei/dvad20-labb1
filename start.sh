sudo pip3 install -q -r requirements.txt
sudo mn -c
# sudo python3 evaluate.py
sudo python3 plot_results.py data20mbps.csv --title "20 Mbps"
sudo python3 plot_results.py data80mbps.csv --title "80 Mbps (Edge-Aggregation)"
sudo python3 plot_results.py data160mbps.csv --title "160 Mbps (Aggregation-Core)"
