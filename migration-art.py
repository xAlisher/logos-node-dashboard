#!/usr/bin/env python3
# run: python3 logos-blockchain-runbook/migration-art.py

R  = "\033[0m"
B  = "\033[1m"
DIM= "\033[2m"
CY = "\033[96m"
YL = "\033[93m"
GR = "\033[92m"
RD = "\033[91m"
BL = "\033[94m"
GY = "\033[90m"
WH = "\033[97m"

print(f"""
{BL}{B}╔══════════════════════════════════════════════╗
║   LOGOS NODE + DASHBOARD  MIGRATION          ║
║   {GY}2026-05-08  //  ~3 min downtime{BL}             ║
╚══════════════════════════════════════════════╝{R}

  {YL}{B}WILD{R}  {GY}dev laptop  (source){R}
  {GY}┌──────────────────────────────────────────┐{R}
  {GY}│{R}  {RD}●{R} logos-node       {GY}:8080{R}               {GY}│{R}
  {GY}│{R}  {RD}●{R} zone-board                            {GY}│{R}
  {GY}│{R}  {RD}●{R} dashboard        {GY}:8090{R}               {GY}│{R}
  {GY}│{R}  {RD}●{R} zone-scanner                          {GY}│{R}
  {GY}│{R}                                          {GY}│{R}
  {GY}│{R}  {GY}systemd: logos-node.service             {GY}│{R}
  {GY}│{R}  {GY}Restart=always  ← had to disable this   {GY}│{R}
  {GY}└──────────────────────────────────────────┘{R}
           {RD}stopped + disabled{R}

           {BL}│{R}  rsync 150 MB chain DB
           {BL}│{R}  ~2s over LAN
           {BL}▼{R}

  {GR}{B}SNEG{R}  {GY}always-on server  (destination){R}
  {GY}┌──────────────────────────────────────────┐{R}
  {GY}│{R}  {GR}●{R} logos-node       {YL}:8085{R} {GY}★ port conflict{R}  {GY}│{R}
  {GY}│{R}  {GR}●{R} zone-board                            {GY}│{R}
  {GY}│{R}  {GR}●{R} dashboard        {GR}:8090{R}               {GY}│{R}
  {GY}│{R}  {GR}●{R} zone-scanner                          {GY}│{R}
  {GY}│{R}                                          {GY}│{R}
  {GY}│{R}  {GY}Ryzen 9 5950X  64 GB RAM  RTX 3090    {GY}│{R}
  {GY}│{R}  {GY}1.8 TB HDD  /mnt/tc-hdd               {GY}│{R}
  {GY}└──────────────────────────────────────────┘{R}
           {GR}online  24/7{R}

  {YL}★{R}  {GY}:8080 taken by Open WebUI (uvicorn){R}
     {GY}"excuse me, I live here" — port 8080, probably{R}

  {GY}──────────────────────────────────────────────{R}
  {WH}post-migration{R}

  {GR}✓{R} height   {CY}114,094{R}    {GR}✓{R} peers   {CY}25 connected{R}
  {GR}✓{R} mode     {CY}Online{R}     {GR}✓{R} wallet  {CY}1,001,000{R}
  {GR}✓{R} zone-board  {CY}tmux: zone-board{R}
  {GR}✓{R} dashboard   {CY}192.168.1.45:8090{R}

  {GY}──────────────────────────────────────────────{R}
  {DIM}github.com/xAlisher/logos-node-dashboard{R}
  {DIM}notes/node-dashboard-migration.md{R}
""")
