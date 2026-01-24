#!/bin/bash

# Copy data for three runs to remote server
# Server: adriel2@188.165.206.77
# Remote dir: ~/Documents/cobex/benchmark-packaging

# Runs to copy:
# - Gaspacho_20260124_151954
# - Chips_à_lancienne_20260124_152124
# - Gel_hydroalcoolique_20260124_152559

echo "Copying run data to remote server..."

# OPTION 1: Using rsync (recommended - preserves structure)
# Uncomment to use:
# rsync -avz --include='*Gaspacho*20260124_151954*' \
#            --include='*Chips_à_lancienne*20260124_152124*' \
#            --include='*Gel_hydroalcoolique*20260124_152559*' \
#            --include='*/' \
#            --exclude='*' \
#            data/output/ \
#            adriel2@188.165.206.77:~/Documents/cobex/benchmark-packaging/data/output/

# OPTION 2: Using tar+ssh (single command, preserves structure) - RECOMMENDED
tar czf - \
  data/output/*Gaspacho*20260124_151954* \
  data/output/*Chips_à_lancienne*20260124_152124* \
  data/output/*Gel_hydroalcoolique*20260124_152559* \
  data/output/images/Gaspacho_20260124_151954 \
  data/output/images/Chips_à_lancienne_20260124_152124 \
  data/output/images/Gel_hydroalcoolique_20260124_152559 \
  data/output/analysis/*Gaspacho*20260124_151954* \
  data/output/analysis/*Chips_à_lancienne*20260124_152124* \
  data/output/analysis/*Gel_hydroalcoolique*20260124_152559* \
  | ssh adriel2@188.165.206.77 'cd ~/Documents/cobex/benchmark-packaging && tar xzf -'

# OPTION 3: Multiple scp commands (clearest, easiest to verify)
# Uncomment to use:
# echo "Copying JSON/CSV files from output root..."
# scp data/output/*Gaspacho*20260124_151954* \
#     data/output/*Chips_à_lancienne*20260124_152124* \
#     data/output/*Gel_hydroalcoolique*20260124_152559* \
#     adriel2@188.165.206.77:~/Documents/cobex/benchmark-packaging/data/output/
#
# echo "Copying analysis files..."
# scp data/output/analysis/*Gaspacho*20260124_151954* \
#     data/output/analysis/*Chips_à_lancienne*20260124_152124* \
#     data/output/analysis/*Gel_hydroalcoolique*20260124_152559* \
#     adriel2@188.165.206.77:~/Documents/cobex/benchmark-packaging/data/output/analysis/
#
# echo "Copying image directories..."
# scp -r data/output/images/Gaspacho_20260124_151954 \
#        data/output/images/Chips_à_lancienne_20260124_152124 \
#        data/output/images/Gel_hydroalcoolique_20260124_152559 \
#        adriel2@188.165.206.77:~/Documents/cobex/benchmark-packaging/data/output/images/

echo "Copy complete!"
