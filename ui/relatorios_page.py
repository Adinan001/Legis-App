# ui/relatorios_page.py
import os
from datetime import date
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QFileDialog, QMessageBox,
                             QFrame, QGridLayout, QSizePolicy, QDateEdit,
                             QLineEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt6.QtGui import QFont
from config import COLORS, MESES
from ui.widgets import btn_primario, label_titulo, separador_h
from core.database import (buscar_processos, buscar_clientes, buscar_lancamentos,
                           buscar_resumo_mensal, buscar_anos_disponiveis,
                           buscar_processos_por_cliente)


class GeradorPDF(QThread):
    concluido = pyqtSignal(str)
    erro      = pyqtSignal(str)

    def __init__(self, tipo, caminho, ano=None, mes=None, cliente=None,
                 data_ini=None, data_fim=None):
        super().__init__()
        self.tipo = tipo; self.caminho = caminho
        self.ano = ano; self.mes = mes
        self.cliente = cliente
        self.data_ini = data_ini; self.data_fim = data_fim

    def run(self):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors as rl_colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                            Paragraph, Spacer, HRFlowable)

            doc = SimpleDocTemplate(self.caminho, pagesize=A4,
                                    rightMargin=2*cm, leftMargin=2*cm,
                                    topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            verde      = rl_colors.HexColor("#3A6B40")
            cinza      = rl_colors.HexColor("#5A6B5C")
            cinza_cl   = rl_colors.HexColor("#F0F5F0")
            vermelho   = rl_colors.HexColor("#C0392B")
            azul       = rl_colors.HexColor("#2563EB")

            tit_st  = ParagraphStyle("t", parent=styles["Heading1"],
                                     textColor=verde, fontSize=18, spaceAfter=4)
            sub_st  = ParagraphStyle("s", parent=styles["Normal"],
                                     textColor=cinza, fontSize=10, spaceAfter=10)
            sec_st  = ParagraphStyle("sec", parent=styles["Heading2"],
                                     textColor=verde, fontSize=13, spaceAfter=6)

            def rodape(titulo_txt, sub_txt):
                el = []
                el.append(Paragraph("<b>LEGIS</b> — Sistema de Gestão Jurídica", sub_st))
                el.append(Paragraph(titulo_txt, tit_st))
                el.append(Paragraph(sub_txt, sub_st))
                el.append(HRFlowable(width="100%", thickness=2, color=verde, spaceAfter=14))
                return el

            def tbl(headers, linhas, widths=None):
                data = [headers] + (linhas if linhas else [["—"] * len(headers)])
                t = Table(data, colWidths=widths, repeatRows=1)
                t.setStyle(TableStyle([
                    ("BACKGROUND",    (0,0),(-1,0), verde),
                    ("TEXTCOLOR",     (0,0),(-1,0), rl_colors.white),
                    ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
                    ("FONTSIZE",      (0,0),(-1,0), 9),
                    ("ALIGN",         (0,0),(-1,0), "CENTER"),
                    ("ROWBACKGROUNDS",(0,1),(-1,-1),[rl_colors.white, cinza_cl]),
                    ("FONTSIZE",      (0,1),(-1,-1), 8),
                    ("TEXTCOLOR",     (0,1),(-1,-1), rl_colors.HexColor("#1A2B1C")),
                    ("GRID",          (0,0),(-1,-1), 0.5, rl_colors.HexColor("#D6DDD7")),
                    ("TOPPADDING",    (0,0),(-1,-1), 6),
                    ("BOTTOMPADDING", (0,0),(-1,-1), 6),
                    ("LEFTPADDING",   (0,0),(-1,-1), 8),
                    ("RIGHTPADDING",  (0,0),(-1,-1), 8),
                ]))
                return t

            def fmt(v):
                return f"R$ {abs(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")

            hoje = date.today().strftime("%d/%m/%Y")
            el = []

            # ── RELATÓRIO POR CLIENTE ──────────────────────────
            if self.tipo == "cliente":
                nome = self.cliente or "—"
                periodo = ""
                if self.data_ini and self.data_fim:
                    di = "/".join(self.data_ini.split("-")[::-1])
                    df = "/".join(self.data_fim.split("-")[::-1])
                    periodo = f"Período: {di} a {df}"

                el += rodape(f"Relatório do Cliente", f"{nome}  •  {periodo}  •  Gerado em {hoje}")

                # Dados do cliente
                clientes = buscar_clientes()
                cli_dados = next((c for c in clientes if c["nome"] == nome), None)
                if cli_dados:
                    info = [
                        ["Nome / Razão Social", cli_dados["nome"]],
                        ["Tipo",                cli_dados["tipo"]],
                        ["CPF / CNPJ",          cli_dados["documento"]],
                        ["Telefone",            cli_dados["contato"]],
                        ["E-mail",              cli_dados.get("email","—")],
                    ]
                    t_info = Table(info, colWidths=[5*cm, 11*cm])
                    t_info.setStyle(TableStyle([
                        ("FONTNAME",     (0,0),(0,-1), "Helvetica-Bold"),
                        ("TEXTCOLOR",    (0,0),(0,-1), cinza),
                        ("FONTSIZE",     (0,0),(-1,-1), 9),
                        ("TOPPADDING",   (0,0),(-1,-1), 5),
                        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
                        ("LINEBELOW",    (0,0),(-1,-1), 0.5, rl_colors.HexColor("#D6DDD7")),
                    ]))
                    el.append(t_info)
                    el.append(Spacer(1, 0.6*cm))

                # Processos vinculados
                el.append(Paragraph("<b>PROCESSOS VINCULADOS</b>", sec_st))
                procs = buscar_processos_por_cliente(nome)

                # Filtrar por período se informado
                if self.data_ini and self.data_fim:
                    procs = [p for p in procs
                             if (not p.get("data_distribuicao") or
                                 self.data_ini <= self._conv_data(p.get("data_distribuicao","")) <= self.data_fim)]

                h = ["Nº Processo", "Área / Ação", "Distribuição", "Status"]
                linhas = [[p["numero"], p["acao"],
                           p.get("data_distribuicao","—"), p["status"]] for p in procs]
                el.append(tbl(h, linhas, widths=[5.5*cm, 4*cm, 2.5*cm, 4.5*cm]))
                el.append(Spacer(1, 0.4*cm))
                el.append(Paragraph(f"Total de processos: <b>{len(procs)}</b>", sub_st))

            # ── PROCESSOS ─────────────────────────────────────
            elif self.tipo == "processos":
                el += rodape("Relatório de Processos", f"Gerado em {hoje}")
                dados = buscar_processos()
                h = ["Nº Processo", "Cliente", "Área / Ação", "Distribuição", "Status"]
                l = [[p["numero"], p["cliente"], p["acao"],
                      p.get("data_distribuicao","—"), p["status"]] for p in dados]
                el.append(tbl(h, l, widths=[4.5*cm,3.5*cm,3*cm,2.5*cm,3*cm]))
                el.append(Spacer(1,0.4*cm))
                el.append(Paragraph(f"Total: <b>{len(dados)}</b> processos", sub_st))

            # ── CLIENTES ──────────────────────────────────────
            elif self.tipo == "clientes":
                el += rodape("Relatório de Clientes", f"Gerado em {hoje}")
                dados = buscar_clientes()
                h = ["Nome / Razão Social", "Tipo", "CPF / CNPJ", "Telefone", "E-mail"]
                l = [[c["nome"], c["tipo"], c["documento"],
                      c["contato"], c.get("email","—")] for c in dados]
                el.append(tbl(h, l, widths=[4*cm,2.5*cm,3.5*cm,3*cm,3.5*cm]))
                el.append(Spacer(1,0.4*cm))
                el.append(Paragraph(f"Total: <b>{len(dados)}</b> clientes", sub_st))

            # ── FINANCEIRO ────────────────────────────────────
            elif self.tipo == "financeiro":
                periodo = f"{MESES[self.mes-1]} de {self.ano}" if self.mes else f"Ano {self.ano}"
                el += rodape("Relatório Financeiro", f"{periodo} — Gerado em {hoje}")
                if self.mes:
                    from core.database import buscar_lancamentos_mes
                    dados = buscar_lancamentos_mes(self.ano, self.mes)
                else:
                    todos = buscar_lancamentos()
                    dados = [l for l in todos if l["data"].startswith(str(self.ano))]
                h = ["Data", "Descrição", "Tipo", "Valor"]
                total_rec = total_des = 0.0
                linhas = []
                for l in dados:
                    data_br = "/".join(l["data"].split("-")[::-1]) if "-" in l["data"] else l["data"]
                    vf = fmt(l["valor"])
                    linhas.append([data_br, l["descricao"], l["tipo"], vf])
                    if l["tipo"] == "Receita": total_rec += l["valor"]
                    else: total_des += l["valor"]
                el.append(tbl(h, linhas, widths=[2.5*cm,7*cm,2.5*cm,3.5*cm]))
                el.append(Spacer(1,0.5*cm))
                resumo = [["Total Recebido", fmt(total_rec)],
                          ["Total Despesas", fmt(total_des)],
                          ["Saldo Líquido",  fmt(total_rec-total_des)]]
                tr = Table(resumo, colWidths=[6*cm,4*cm])
                tr.setStyle(TableStyle([
                    ("FONTNAME",     (0,0),(-1,-1),"Helvetica-Bold"),
                    ("FONTSIZE",     (0,0),(-1,-1),10),
                    ("TEXTCOLOR",    (0,0),(0,-1),cinza),
                    ("TEXTCOLOR",    (1,0),(1,0),rl_colors.HexColor("#27AE60")),
                    ("TEXTCOLOR",    (1,1),(1,1),vermelho),
                    ("TEXTCOLOR",    (1,2),(1,2),azul),
                    ("ALIGN",        (1,0),(1,-1),"RIGHT"),
                    ("LINEABOVE",    (0,2),(-1,2),1,verde),
                    ("TOPPADDING",   (0,0),(-1,-1),6),
                    ("BOTTOMPADDING",(0,0),(-1,-1),6),
                ]))
                el.append(tr)

            # ── COMPLETO ──────────────────────────────────────
            elif self.tipo == "completo":
                el += rodape("Relatório Completo do Escritório", f"Gerado em {hoje}")
                el.append(Paragraph("<b>PROCESSOS</b>", sec_st))
                procs = buscar_processos()
                el.append(tbl(["Nº Processo","Cliente","Área","Status"],
                              [[p["numero"],p["cliente"],p["acao"],p["status"]] for p in procs],
                              widths=[5*cm,4*cm,3.5*cm,4*cm]))
                el.append(Spacer(1,0.8*cm))
                el.append(Paragraph("<b>CLIENTES</b>", sec_st))
                clis = buscar_clientes()
                el.append(tbl(["Nome","Tipo","CPF/CNPJ","Contato"],
                              [[c["nome"],c["tipo"],c["documento"],c["contato"]] for c in clis],
                              widths=[5*cm,3*cm,4*cm,4.5*cm]))
                el.append(Spacer(1,0.8*cm))
                el.append(Paragraph(f"<b>FINANCEIRO — {self.ano}</b>", sec_st))
                resumo = buscar_resumo_mensal(self.ano)
                abrevs = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
                el.append(tbl(["Mês","Receitas","Despesas","Saldo"],
                              [[abrevs[m["mes"]-1],fmt(m["receita"]),fmt(m["despesa"]),fmt(m["saldo"])] for m in resumo],
                              widths=[3*cm,4*cm,4*cm,4*cm]))

            doc.build(el)
            self.concluido.emit(self.caminho)

        except Exception as e:
            import traceback
            self.erro.emit(traceback.format_exc())

    def _conv_data(self, d):
        """Converte DD/MM/AAAA para AAAA-MM-DD para comparação."""
        if "/" in d:
            parts = d.split("/")
            if len(parts) == 3:
                return f"{parts[2]}-{parts[1]}-{parts[0]}"
        return d


class CardRelatorio(QFrame):
    clicado = pyqtSignal(str)

    def __init__(self, icone, titulo, descricao, tipo, parent=None):
        super().__init__(parent)
        self.tipo = tipo
        self.setStyleSheet(f"""
            QFrame {{ background: {COLORS['white']}; border: 1.5px solid {COLORS['border']}; border-radius: 10px; }}
            QFrame:hover {{ border-color: {COLORS['accent']}; background: {COLORS['accent_light']}; }}
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(110)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(5)
        topo = QHBoxLayout()
        lbl_ic = QLabel(icone)
        lbl_ic.setFont(QFont("Segoe UI", 22))
        topo.addWidget(lbl_ic)
        topo.addStretch()
        btn = btn_primario("Gerar PDF")
        btn.setFixedHeight(30)
        btn.clicked.connect(lambda: self.clicado.emit(self.tipo))
        topo.addWidget(btn)
        lay.addLayout(topo)
        lbl_t = QLabel(titulo)
        lbl_t.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_t.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        lay.addWidget(lbl_t)
        lbl_d = QLabel(descricao)
        lbl_d.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; border: none;")
        lbl_d.setWordWrap(True)
        lay.addWidget(lbl_d)


class RelatoriosPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        layout.addWidget(label_titulo("Relatórios"))
        sub = QLabel("Gere relatórios em PDF prontos para impressão ou envio.")
        sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(sub)
        layout.addWidget(separador_h())

        # ── FILTROS GERAIS ──
        filtros = QHBoxLayout()
        filtros.addWidget(QLabel("<b>Ano:</b>"))
        self.cb_ano = QComboBox()
        self.cb_ano.setFixedWidth(90)
        self.cb_ano.setStyleSheet(f"padding: 6px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        for a in buscar_anos_disponiveis():
            self.cb_ano.addItem(str(a))
        filtros.addWidget(self.cb_ano)
        filtros.addSpacing(10)
        filtros.addWidget(QLabel("<b>Mês:</b>"))
        self.cb_mes = QComboBox()
        self.cb_mes.setFixedWidth(130)
        self.cb_mes.setStyleSheet(f"padding: 6px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        self.cb_mes.addItem("Ano completo", None)
        for i, m in enumerate(MESES):
            self.cb_mes.addItem(m, i+1)
        filtros.addWidget(self.cb_mes)
        filtros.addStretch()
        layout.addLayout(filtros)

        # ── CARDS DOS RELATÓRIOS GERAIS ──
        grid = QGridLayout()
        grid.setSpacing(14)
        cards_gerais = [
            ("⚖️",  "Processos",         "Todos os processos com status e datas.",                 "processos"),
            ("👥", "Clientes",           "Cadastro completo de clientes.",                         "clientes"),
            ("💰", "Financeiro",         "Lançamentos do período selecionado com totais.",          "financeiro"),
            ("📋", "Relatório Completo", "Processos, clientes e resumo financeiro em um PDF.",      "completo"),
        ]
        for i, (ic, tit, desc, tipo) in enumerate(cards_gerais):
            card = CardRelatorio(ic, tit, desc, tipo)
            card.clicado.connect(self.gerar_relatorio)
            grid.addWidget(card, i//2, i%2)
        layout.addLayout(grid)

        # ── RELATÓRIO POR CLIENTE ──
        layout.addWidget(separador_h())
        layout.addWidget(QLabel("<b>📁  Relatório por Cliente</b>"))

        cli_frame = QFrame()
        cli_frame.setStyleSheet(f"QFrame {{ background: {COLORS['white']}; border: 1.5px solid {COLORS['border']}; border-radius: 10px; }}")
        cli_lay = QVBoxLayout(cli_frame)
        cli_lay.setContentsMargins(20, 16, 20, 16)
        cli_lay.setSpacing(12)

        sub_cli = QLabel("Selecione o cliente e o período para gerar um relatório com todos os processos vinculados.")
        sub_cli.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; border: none;")
        sub_cli.setWordWrap(True)
        cli_lay.addWidget(sub_cli)

        linha_cli = QHBoxLayout()
        linha_cli.setSpacing(12)

        linha_cli.addWidget(QLabel("<b>Cliente:</b>"))
        self.cb_cliente = QComboBox()
        self.cb_cliente.setMinimumWidth(220)
        self.cb_cliente.setStyleSheet(f"padding: 7px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        self._preencher_clientes()
        linha_cli.addWidget(self.cb_cliente)

        linha_cli.addWidget(QLabel("<b>De:</b>"))
        self.data_ini = QDateEdit()
        self.data_ini.setCalendarPopup(True)
        self.data_ini.setDate(QDate(date.today().year, 1, 1))
        self.data_ini.setDisplayFormat("dd/MM/yyyy")
        self.data_ini.setStyleSheet(f"padding: 7px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        linha_cli.addWidget(self.data_ini)

        linha_cli.addWidget(QLabel("<b>Até:</b>"))
        self.data_fim = QDateEdit()
        self.data_fim.setCalendarPopup(True)
        self.data_fim.setDate(QDate.currentDate())
        self.data_fim.setDisplayFormat("dd/MM/yyyy")
        self.data_fim.setStyleSheet(f"padding: 7px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        linha_cli.addWidget(self.data_fim)

        btn_cli = btn_primario("📄  Gerar PDF do Cliente")
        btn_cli.clicked.connect(lambda: self.gerar_relatorio("cliente"))
        linha_cli.addWidget(btn_cli)
        linha_cli.addStretch()
        cli_lay.addLayout(linha_cli)
        layout.addWidget(cli_frame)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        layout.addWidget(self.lbl_status)
        layout.addStretch()

    def _preencher_clientes(self):
        self.cb_cliente.clear()
        try:
            for c in buscar_clientes():
                self.cb_cliente.addItem(c["nome"], c["nome"])
        except Exception:
            pass

    def gerar_relatorio(self, tipo):
        ano = int(self.cb_ano.currentText()) if self.cb_ano.currentText() else date.today().year
        mes = self.cb_mes.currentData()
        cliente = self.cb_cliente.currentData() if tipo == "cliente" else None
        data_ini = self.data_ini.date().toString("yyyy-MM-dd") if tipo == "cliente" else None
        data_fim = self.data_fim.date().toString("yyyy-MM-dd") if tipo == "cliente" else None

        nomes = {
            "processos":  f"Legis_Processos_{date.today().strftime('%Y%m%d')}.pdf",
            "clientes":   f"Legis_Clientes_{date.today().strftime('%Y%m%d')}.pdf",
            "financeiro": f"Legis_Financeiro_{ano}_{mes or 'Anual'}_{date.today().strftime('%Y%m%d')}.pdf",
            "completo":   f"Legis_Completo_{date.today().strftime('%Y%m%d')}.pdf",
            "cliente":    f"Legis_Cliente_{(cliente or 'SemNome').replace(' ','_')}_{date.today().strftime('%Y%m%d')}.pdf",
        }
        from ui.widgets import dialogo_salvar
        caminho = dialogo_salvar(self, "Salvar Relatório PDF",
            nomes.get(tipo, "relatorio.pdf"), "PDF (*.pdf)")
        if not caminho:
            return

        self.lbl_status.setText("⏳  Gerando PDF...")
        self.lbl_status.setStyleSheet(f"color: {COLORS['blue']}; font-size: 12px; font-weight: 600;")

        if self.worker and self.worker.isRunning():
            self.worker.quit(); self.worker.wait()

        self.worker = GeradorPDF(tipo, caminho, ano=ano, mes=mes,
                                  cliente=cliente, data_ini=data_ini, data_fim=data_fim)
        self.worker.concluido.connect(self._pdf_pronto)
        self.worker.erro.connect(self._pdf_erro)
        self.worker.start()

    def _pdf_pronto(self, caminho):
        self.lbl_status.setText("✅  PDF gerado com sucesso!")
        self.lbl_status.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px; font-weight: 600;")
        resp = QMessageBox.question(self, "PDF Gerado",
            f"Relatório salvo em:\n{caminho}\n\nDeseja abrir agora?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            import subprocess
            subprocess.Popen(["start", "", caminho], shell=True)

    def _pdf_erro(self, msg):
        self.lbl_status.setText("❌  Erro ao gerar PDF.")
        self.lbl_status.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px; font-weight: 600;")
        QMessageBox.critical(self, "Erro", f"Não foi possível gerar o PDF:\n{msg[:300]}")
