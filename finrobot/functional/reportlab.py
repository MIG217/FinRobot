import os
import traceback
from reportlab.lib import colors
from reportlab.lib import pagesizes
from reportlab.platypus import (
    SimpleDocTemplate,
    Frame,
    Paragraph,
    Image,
    PageTemplate,
    FrameBreak,
    Spacer,
    Table,
    TableStyle,
    NextPageTemplate,
    PageBreak,
)
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import pandas as pd

# Attempt to register a common system font for Chinese
# Option 1: SimSun (common on Windows)
try:
    # For .ttc files, you might need to specify subfontIndex if it's a collection
    # Check common paths for simsun.ttc
    font_path_simsun_ttc = ""
    if os.path.exists("C:/Windows/Fonts/simsun.ttc"):
        font_path_simsun_ttc = "C:/Windows/Fonts/simsun.ttc"
    elif os.path.exists("/usr/share/fonts/truetype/simsun/simsun.ttc"): # Common on some Linux
        font_path_simsun_ttc = "/usr/share/fonts/truetype/simsun/simsun.ttc"
    
    if font_path_simsun_ttc:
        pdfmetrics.registerFont(TTFont('SimSun', font_path_simsun_ttc, subfontIndex=0)) # Assuming first font in collection
        pdfmetrics.registerFont(TTFont('SimSun-Bold', font_path_simsun_ttc, subfontIndex=0)) # ReportLab doesn't auto-bold TTF, find a bold version or use same for now
        FONT_NAME = 'SimSun'
        FONT_NAME_BOLD = 'SimSun-Bold'
        print("Registered SimSun font.")
    else:
        raise FileNotFoundError("SimSun font not found in common locations.")

except Exception as e_simsun:
    print(f"Could not register SimSun: {e_simsun}. Trying Noto Sans CJK SC.")
    # Option 2: Noto Sans CJK SC (assumes font files are in a 'fonts' subdirectory or installable)
    # Create a 'fonts' directory in the project root if it doesn't exist.
    # The user/developer would need to place NotoSansCJKsc-Regular.otf and NotoSansCJKsc-Bold.otf there.
    # Or the worker could try to download them.
    # For now, let's assume they are available or can be installed.
    # This part might require the worker to ensure the font files exist.
    # For simplicity in this instruction, we'll just define the names
    # and assume the actual font registration might need manual setup by the user if files aren't there.
    
    # Placeholder: In a real scenario, ensure NotoSansCJKsc-Regular.otf and NotoSansCJKsc-Bold.otf
    # are available. The worker could try to install them using system commands if possible.
    # E.g. on Debian/Ubuntu: apt-get install -y fonts-noto-cjk
    # For now, we'll just define the font names and the code will fail if they aren't truly registered.
    try:
        # This is a simplified assumption. The worker might need to install these fonts.
        # For example:
        # pdfmetrics.registerFont(TTFont('NotoSansCJKsc-Regular', 'path/to/NotoSansCJKsc-Regular.otf'))
        # pdfmetrics.registerFont(TTFont('NotoSansCJKsc-Bold', 'path/to/NotoSansCJKsc-Bold.otf'))
        # FONT_NAME = 'NotoSansCJKsc-Regular'
        # FONT_NAME_BOLD = 'NotoSansCJKsc-Bold'
        # For the purpose of this subtask, let's assume the worker will attempt to install
        # fonts-noto-cjk via apt-get if SimSun is not found.
        # If that also fails, it should fall back to Helvetica and report the issue.

        # Simulate checking for Noto fonts (worker should implement actual check/install)
        # This is a placeholder for the worker's logic to find/install Noto.
        # On the worker side, it should try `apt-get update && apt-get install -y fonts-noto-cjk`
        # Then the actual paths would be something like:
        # '/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf'
        # '/usr/share/fonts/opentype/noto/NotoSansCJKsc-Bold.otf'
        noto_regular_path = '/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf'
        noto_bold_path = '/usr/share/fonts/opentype/noto/NotoSansCJKsc-Bold.otf'

        if os.path.exists(noto_regular_path) and os.path.exists(noto_bold_path):
            pdfmetrics.registerFont(TTFont('NotoSansCJKsc-Regular', noto_regular_path))
            pdfmetrics.registerFont(TTFont('NotoSansCJKsc-Bold', noto_bold_path))
            FONT_NAME = 'NotoSansCJKsc-Regular'
            FONT_NAME_BOLD = 'NotoSansCJKsc-Bold'
            print("Registered Noto Sans CJK SC font.")
        else:
            # Fallback if no Chinese font can be registered
            print("Noto Sans CJK SC font not found. Falling back to Helvetica. Chinese characters will not render correctly.")
            FONT_NAME = 'Helvetica'
            FONT_NAME_BOLD = 'Helvetica-Bold'
    except Exception as e_noto:
        print(f"Could not register Noto Sans CJK SC: {e_noto}. Falling back to Helvetica. Chinese characters will not render correctly.")
        FONT_NAME = 'Helvetica'
        FONT_NAME_BOLD = 'Helvetica-Bold'

from ..data_source import FMPUtils, YFinanceUtils
from .analyzer import ReportAnalysisUtils
from typing import Annotated


class ReportLabUtils:

    def build_annual_report(
        ticker_symbol: Annotated[str, "ticker symbol"],
        save_path: Annotated[str, "path to save the annual report pdf"],
        operating_results: Annotated[
            str,
            "a paragraph of text: the company's income summarization from its financial report",
        ],
        market_position: Annotated[
            str,
            "a paragraph of text: the company's current situation and end market (geography), major customers (blue chip or not), market share from its financial report, avoid similar sentences also generated in the business overview section, classify it into either of the two",
        ],
        business_overview: Annotated[
            str,
            "a paragraph of text: the company's description and business highlights from its financial report",
        ],
        risk_assessment: Annotated[
            str,
            "a paragraph of text: the company's risk assessment from its financial report",
        ],
        competitors_analysis: Annotated[
            str,
            "a paragraph of text: the company's competitors analysis from its financial report and competitors' financial report",
        ],
        share_performance_image_path: Annotated[
            str, "path to the share performance image"
        ],
        pe_eps_performance_image_path: Annotated[
            str, "path to the PE and EPS performance image"
        ],
        filing_date: Annotated[str, "filing date of the analyzed financial report"],
    ) -> str:
        """
        Aggregate a company's business_overview, market_position, operating_results,
        risk assessment, competitors analysis and share performance, PE & EPS performance charts all into a PDF report.
        """
        try:
            # 2. 创建PDF并插入图像
            # 页面设置
            page_width, page_height = pagesizes.A4
            left_column_width = page_width * 2 / 3
            right_column_width = page_width - left_column_width
            margin = 4

            # 创建PDF文档路径
            pdf_path = (
                os.path.join(save_path, f"{ticker_symbol}_Equity_Research_report.pdf")
                if os.path.isdir(save_path)
                else save_path
            )
            # Ensure directory exists if pdf_path includes a directory
            pdf_dir = os.path.dirname(pdf_path)
            if pdf_dir: # Only call makedirs if a directory part exists
                os.makedirs(pdf_dir, exist_ok=True)
            doc = SimpleDocTemplate(pdf_path, pagesize=pagesizes.A4)
        


            # 定义两个栏位的Frame
            frame_left = Frame(
                margin,
                margin,
                left_column_width - margin * 2,
                page_height - margin * 2,
                id="left",
            )
            frame_right = Frame(
                left_column_width,
                margin,
                right_column_width - margin * 2,
                page_height - margin * 2,
                id="right",
            )

            single_frame = Frame(margin, margin, page_width-margin*2, page_height-margin*2, id='single')
            single_column_layout = PageTemplate(id='OneCol', frames=[single_frame])

            left_column_width_p2 = (page_width - margin * 3) // 2
            right_column_width_p2 = left_column_width_p2
            frame_left_p2 = Frame(
                margin,
                margin,
                left_column_width_p2 - margin * 2,
                page_height - margin * 2,
                id="left",
            )
            frame_right_p2 = Frame(
                left_column_width_p2,
                margin,
                right_column_width_p2 - margin * 2,
                page_height - margin * 2,
                id="right",
            )

            #创建PageTemplate，并添加到文档
            page_template = PageTemplate(
                id="TwoColumns", frames=[frame_left, frame_right]
            )
            page_template_p2 = PageTemplate(
                id="TwoColumns_p2", frames=[frame_left_p2, frame_right_p2]
            )

             #Define single column Frame
            single_frame = Frame(
                margin,
                margin,
                page_width - 2 * margin,
                page_height - 2 * margin,
                id="single",
            )

            # Create a PageTemplate with a single column
            single_column_layout = PageTemplate(id="OneCol", frames=[single_frame])

            doc.addPageTemplates([page_template, single_column_layout, page_template_p2])

            styles = getSampleStyleSheet()

            # 自定义样式
            custom_style = ParagraphStyle(
                name="Custom",
                parent=styles["Normal"],
                fontName=FONT_NAME,
                fontSize=10,
                # leading=15,
                alignment=TA_JUSTIFY,
            )

            title_style = ParagraphStyle(
                name="TitleCustom",
                parent=styles["Title"],
                fontName=FONT_NAME_BOLD,
                fontSize=16,
                leading=20,
                alignment=TA_LEFT,
                spaceAfter=10,
            )

            subtitle_style = ParagraphStyle(
                name="Subtitle",
                parent=styles["Heading2"],
                fontName=FONT_NAME_BOLD,
                fontSize=14,
                leading=12,
                alignment=TA_LEFT,
                spaceAfter=6,
            )

            table_style2 = TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.white),
                    ("FONT", (0, 0), (-1, -1), FONT_NAME, 7),
                    ("FONT", (0, 0), (-1, 0), FONT_NAME_BOLD, 14),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    # 所有单元格左对齐
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    # 标题栏下方添加横线
                    ("LINEBELOW", (0, 0), (-1, 0), 2, colors.black),
                    # 表格最下方添加横线
                    ("LINEBELOW", (0, -1), (-1, -1), 2, colors.black),
                ]
            )

            stock_info = YFinanceUtils.get_stock_info(ticker_symbol)
            name = stock_info.get("shortName", ticker_symbol) # Use ticker_symbol as fallback

            # 准备左栏和右栏内容
            content = []
            # 标题
            content.append(
                Paragraph(
                    f"Equity Research Report: {name}",
                    title_style,
                )
            )

            # 子标题
            content.append(Paragraph("Business Overview", subtitle_style))
            content.append(Paragraph(business_overview, custom_style))

            content.append(Paragraph("Market Position", subtitle_style))
            content.append(Paragraph(market_position, custom_style))
            
            content.append(Paragraph("Operating Results", subtitle_style))
            content.append(Paragraph(operating_results, custom_style))

            # content.append(Paragraph("Summarization", subtitle_style))
            df = FMPUtils.get_financial_metrics(ticker_symbol, years=5)
            
            if df is None:
                print("Warning: FMPUtils.get_financial_metrics returned None. Using empty DataFrame for financial metrics table.")
                df = pd.DataFrame() # Create an empty DataFrame

            df.reset_index(inplace=True) # Creates 'index' column
            
            stock_info_currency = YFinanceUtils.get_stock_info(ticker_symbol)
            currency = stock_info_currency.get("currency", "USD") # Fallback currency
            
            df.rename(columns={"index": f"FY ({currency} mn)"}, inplace=True)

            table_data = [["Financial Metrics"]]
            table_data += [df.columns.to_list()] + df.values.tolist() # Will be [f"FY ({currency} mn)"] and [] if df was empty

            num_cols = df.shape[1] # Will be 1 if df was empty and reset_index + rename occurred
            if num_cols > 0:
                col_widths = [(left_column_width - margin * 4) / num_cols] * num_cols
            else:
                # This case should ideally not be reached if df always gets at least one column after rename
                # but as a safeguard:
                col_widths = [left_column_width - margin * 4]
                if not df.columns.to_list() and len(table_data) == 1: # only [["Financial Metrics"]]
                     table_data.append(["No Data Available"]) # Add a row to prevent empty table error
            table = Table(table_data, colWidths=col_widths)
            table.setStyle(table_style2)
            content.append(table)

            content.append(FrameBreak())  # 用于从左栏跳到右栏

            table_style = TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.white),
                    ("FONT", (0, 0), (-1, -1), FONT_NAME, 8),
                    ("FONT", (0, 0), (-1, 0), FONT_NAME_BOLD, 12),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    # 第一列左对齐
                    ("ALIGN", (0, 1), (0, -1), "LEFT"),
                    # 第二列右对齐
                    ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                    # 标题栏下方添加横线
                    ("LINEBELOW", (0, 0), (-1, 0), 2, colors.black),
                ]
            )
            full_length = right_column_width - 2 * margin

            data = [
                ["FinRobot"],
                ["https://ai4finance.org/"],
                ["https://github.com/AI4Finance-Foundation/FinRobot"],
                [f"Report date: {filing_date}"],
            ]
            col_widths = [full_length]
            table = Table(data, colWidths=col_widths)
            table.setStyle(table_style)
            content.append(table)

            # content.append(Paragraph("", custom_style))
            content.append(Spacer(1, 0.15 * inch))
            key_data = ReportAnalysisUtils.get_key_data(ticker_symbol, filing_date)
            # 表格数据
            data = [["Key data", ""]]
            data += [[k, v] for k, v in key_data.items()]
            col_widths = [full_length // 3 * 2, full_length // 3]
            table = Table(data, colWidths=col_widths)
            table.setStyle(table_style)
            content.append(table)

            # 将Matplotlib图像添加到右栏

            # 历史股价
            data = [["Share Performance"]]
            col_widths = [full_length]
            table = Table(data, colWidths=col_widths)
            table.setStyle(table_style)
            content.append(table)

            plot_path = share_performance_image_path
            width = right_column_width
            height = width // 2
            content.append(Image(plot_path, width=width, height=height))

            # 历史PE和EPS
            data = [["PE & EPS"]]
            col_widths = [full_length]
            table = Table(data, colWidths=col_widths)
            table.setStyle(table_style)
            content.append(table)

            plot_path = pe_eps_performance_image_path
            width = right_column_width
            height = width // 2
            content.append(Image(plot_path, width=width, height=height))

            # # 开始新的一页
            content.append(NextPageTemplate("OneCol"))
            content.append(PageBreak())
            
            content.append(Paragraph("Risk Assessment", subtitle_style))
            content.append(Paragraph(risk_assessment, custom_style))

            content.append(Paragraph("Competitors Analysis", subtitle_style))
            content.append(Paragraph(competitors_analysis, custom_style))
            # def add_table(df, title):
            #     df = df.applymap(lambda x: "{:.2f}".format(x) if isinstance(x, float) else x)
            #     # df.columns = [col.strftime('%Y') for col in df.columns]
            #     # df.reset_index(inplace=True)
            #     # currency = ra.info['currency']
            #     df.rename(columns={"index": "segment"}, inplace=True)
            #     table_data = [[title]]
            #     table_data += [df.columns.to_list()] + df.values.tolist()

            #     table = Table(table_data)
            #     table.setStyle(table_style2)
            #     num_columns = len(df.columns)

            #     column_width = (page_width - 4 * margin) / (num_columns + 1)
            #     first_column_witdh = column_width * 2
            #     table._argW = [first_column_witdh] + [column_width] * (num_columns - 1)

            #     content.append(table)
            #     content.append(Spacer(1, 0.15 * inch))

            # if os.path.exists(f"{ra.project_dir}/outer_resource/"):
            #     Revenue10Q = pd.read_csv(
            #         f"{ra.project_dir}/outer_resource/Revenue10Q.csv",
            #     )
            #     # del Revenue10K['FY2018']
            #     # del Revenue10K['FY2019']
            #     add_table(Revenue10Q, "Revenue")

            #     Ratio10Q = pd.read_csv(
            #         f"{ra.project_dir}/outer_resource/Ratio10Q.csv",
            #     )
            #     # del Ratio10K['FY2018']
            #     # del Ratio10K['FY2019']
            #     add_table(Ratio10Q, "Ratio")

            #     Yoy10Q = pd.read_csv(
            #         f"{ra.project_dir}/outer_resource/Yoy10Q.csv",
            #     )
            #     # del Yoy10K['FY2018']
            #     # del Yoy10K['FY2019']
            #     add_table(Yoy10Q, "Yoy")

            #     plot_path = os.path.join(f"{ra.project_dir}/outer_resource/", "segment.png")
            #     width = page_width - 2 * margin
            #     height = width * 3 // 5
            #     content.append(Image(plot_path, width=width, height=height))

            # # 第二页及之后内容，使用单栏布局
            # df = ra.get_income_stmt()
            # df = df[df.columns[:3]]
            # def convert_if_money(value):
            #     if np.abs(value) >= 1000000:
            #         return value / 1000000
            #     else:
            #         return value

            # # 应用转换函数到DataFrame的每列
            # df = df.applymap(convert_if_money)

            # df.columns = [col.strftime('%Y') for col in df.columns]
            # df.reset_index(inplace=True)
            # currency = ra.info['currency']
            # df.rename(columns={'index': f'FY ({currency} mn)'}, inplace=True)  # 可选：重命名索引列为“序号”
            # table_data = [["Income Statement"]]
            # table_data += [df.columns.to_list()] + df.values.tolist()

            # table = Table(table_data)
            # table.setStyle(table_style2)
            # content.append(table)

            # content.append(FrameBreak())  # 用于从左栏跳到右栏

            # df = ra.get_cash_flow()
            # df = df[df.columns[:3]]

            # df = df.applymap(convert_if_money)

            # df.columns = [col.strftime('%Y') for col in df.columns]
            # df.reset_index(inplace=True)
            # currency = ra.info['currency']
            # df.rename(columns={'index': f'FY ({currency} mn)'}, inplace=True)  # 可选：重命名索引列为“序号”
            # table_data = [["Cash Flow Sheet"]]
            # table_data += [df.columns.to_list()] + df.values.tolist()

            # table = Table(table_data)
            # table.setStyle(table_style2)
            # content.append(table)
            # # content.append(Paragraph('This is a single column on the second page', custom_style))
            # # content.append(Spacer(1, 0.2*inch))
            # # content.append(Paragraph('More content in the single column.', custom_style))

            # 构建PDF文档
            doc.build(content)

            return "Annual report generated successfully."

        except Exception:
            return traceback.format_exc()
