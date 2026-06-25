# HCLS Agentic AI Suite — collateral build
# Regenerates console mockups and deployment-handbook PDFs from source.
PYTHON ?= python3
HB     := tooling/handbooks
CONSOLE:= docs/assets/console
AGENTS := deliverables/agent-handbooks

.PHONY: help handbooks figures master agent-handbooks deck decks decks-pdf roi install clean-handbooks \
        build-lambdas deploy

help:
	@echo "HCLS targets:"
	@echo "  -- AWS deployment --"
	@echo "  make build-lambdas   package all agent + connector zips WITH deps (scripts/build_lambdas.sh)"
	@echo "  make deploy AGENT=02-pharmacovigilance CFN_BUCKET=.. CODE_BUCKET=..   stage + deploy quickstart"
	@echo "  -- GTM decks & ROI --"
	@echo "  make decks           build 8 agent + overview + CIO decks (needs npm install) and recompress"
	@echo "  make decks-pdf       export all GTM decks to PDF leave-behinds (needs LibreOffice)"
	@echo "  make roi             regenerate the SA-fillable ROI calculator workbook"
	@echo "  -- collateral --"
	@echo "  make install         pip install the generation toolchain"
	@echo "  make handbooks       regenerate figures + master PDF + all 8 agent PDFs"
	@echo "  make figures         regenerate the generic console mockups"
	@echo "  make master          regenerate the suite master handbook PDF"
	@echo "  make agent-handbooks regenerate the 8 per-agent handbook PDFs"
	@echo "  make deck            export the executive deck PPTX -> PDF (needs LibreOffice)"
	@echo "  make clean-handbooks remove generated PDFs and build stamps"

# --- AWS deployment ----------------------------------------------------------
AGENT       ?= 01-regulatory-writing
ENVIRONMENT ?= dev
GATEWAY_MODE ?= portable
DEPLOY_MODE ?= native

build-lambdas:
	bash scripts/build_lambdas.sh

deploy:
	bash scripts/deploy.sh $(AGENT) $(ENVIRONMENT) $(GATEWAY_MODE) $(DEPLOY_MODE)

install:
	$(PYTHON) -m pip install -r $(HB)/requirements.txt

# --- generic console mockups -------------------------------------------------
figures: $(CONSOLE)/.figures.stamp
$(CONSOLE)/.figures.stamp: $(HB)/gen_console.py
	$(PYTHON) $(HB)/gen_console.py
	@touch $@

# --- suite master handbook PDF ----------------------------------------------
master: HCLS-Deployment-Handbook.pdf
HCLS-Deployment-Handbook.pdf: docs/DEPLOYMENT-HANDBOOK.md $(HB)/build_master_pdf.py $(HB)/handbook.css $(CONSOLE)/.figures.stamp
	$(PYTHON) $(HB)/build_master_pdf.py

# --- per-agent tailored handbook PDFs (profiles live in agent_handbooks.py) --
agent-handbooks: $(AGENTS)/.agents.stamp
$(AGENTS)/.agents.stamp: $(HB)/agent_handbooks.py $(HB)/handbook_template.md $(HB)/handbook.css $(CONSOLE)/.figures.stamp
	$(PYTHON) $(HB)/agent_handbooks.py
	@touch $@

# --- everything --------------------------------------------------------------
handbooks: figures master agent-handbooks
	@echo "Handbooks regenerated: master + $(words $(wildcard $(AGENTS)/*.pdf)) agent PDFs."

# --- executive deck PDF (optional; requires LibreOffice 'soffice') ----------
deck: HCLS-Agentic-AI-Suite-Executive-Overview.pdf
HCLS-Agentic-AI-Suite-Executive-Overview.pdf: HCLS-Agentic-AI-Suite-Executive-Overview.pptx
	soffice --headless --convert-to pdf --outdir . $<

# --- GTM decks (pptxgenjs; requires `npm install`) --------------------------
# Builds 8 agent decks + executive overview + CIO/CISO board deck, then deflate-
# recompresses (pptxgenjs writes uncompressed ZIPs).
decks:
	node decks/build-agent-decks.js
	node decks/build-cio-deck.js
	$(PYTHON) decks/recompress.py

# --- GTM deck PDF leave-behinds (requires LibreOffice 'soffice') ------------
decks-pdf:
	soffice --headless --convert-to pdf --outdir decks decks/HCLS-*.pptx

# --- ROI calculator workbook ------------------------------------------------
roi:
	$(PYTHON) gtm/roi-calculator/generate_roi_calculator.py

clean-handbooks:
	rm -f HCLS-Deployment-Handbook.pdf $(AGENTS)/*.pdf \
	      $(CONSOLE)/.figures.stamp $(AGENTS)/.agents.stamp
