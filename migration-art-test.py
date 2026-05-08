#!/usr/bin/env python3
# run: python3 migration-art-test.py

R  = "\033[0m"
B  = "\033[1m"
DIM= "\033[2m"
CY = "\033[96m"
YL = "\033[93m"
GR = "\033[92m"
RD = "\033[91m"
BL = "\033[94m"
MG = "\033[95m"
GY = "\033[90m"
WH = "\033[97m"

print(f"""
{BL}{B}╔═══════════════════════════════════════════════════════════════════════════╗
║  {CY}LOGOS TESTNET NODE MIGRATION{BL}  //  {GY}2026-05-08  //  ~3 min downtime{BL}        ║
╚═══════════════════════════════════════════════════════════════════════════╝{R}

  {YL}{B}WILD{R}{GY} (dev laptop){R}                           {GR}{B}SNEG{R}{GY} (always-on server){R}

  {GY}┌─────────────────────────┐{R}                {GY}┌──────────────────────────────┐{R}
  {GY}│{R} {RD}●{R} logos-node  {GY}:8080{R}     {GY}│{R}                {GY}│{R} {GR}●{R} logos-node  {YL}:8085{R} {GY}★{R}        {GY}│{R}
  {GY}│{R} {RD}●{R} zone-board            {GY}│{R}                {GY}│{R} {GR}●{R} zone-board                 {GY}│{R}
  {GY}│{R} {RD}●{R} dashboard   {GY}:8090{R}     {GY}│{R}                {GY}│{R} {GR}●{R} dashboard   {GR}:8090{R}          {GY}│{R}
  {GY}│{R} {RD}●{R} zone-scanner          {GY}│{R}  {BL}{B}━━━━━━━━━►  {R}  {GY}│{R} {GR}●{R} zone-scanner               {GY}│{R}
  {GY}│{R}                         {GY}│{R}                {GY}│{R}                              {GY}│{R}
  {GY}└─────────────────────────┘{R}                {GY}└──────────────────────────────┘{R}
        {RD}stopped + disabled{R}                           {GR}online  24/7{R}

  {GY}───────────────────────────────────────────────────────────────────────────{R}

  {BL}rsync chain DB{R}    {GY}150 MB{R}  {BL}━━━━━━━━━━━━━━━━━━━━━{R}  {GR}~2s over LAN{R}

  {YL}{B}★{R}  {GY}:8080 was occupied by Open WebUI (uvicorn){R}
     {GY}"excuse me, I live here" — port 8080, probably{R}

  {GY}───────────────────────────────────────────────────────────────────────────{R}

  {WH}post-migration status{R}

  {GR}✓{R}  height    {CY}114,094{R}          {GR}✓{R}  peers     {CY}25 connected{R}
  {GR}✓{R}  mode      {CY}Online{R}            {GR}✓{R}  wallet    {CY}1,001,000{R}
  {GR}✓{R}  zone-board {CY}tmux: zone-board{R}  {GR}✓{R}  dashboard {CY}192.168.1.45:8090{R}

  {GY}───────────────────────────────────────────────────────────────────────────{R}
  {DIM}docs: github.com/xAlisher/logos-node-dashboard/blob/main/notes/node-dashboard-migration.md{R}
""")
