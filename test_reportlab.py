from finrobot.functional.reportlab import ReportLabUtils
import os
import traceback

# Create dummy image files if they don't exist to avoid ReportLab errors
dummy_share_path = 'dummy_share_performance.png'
dummy_pe_eps_path = 'dummy_pe_eps.png'

# Ensure dummy files are created if not present (though created by bash above)
if not os.path.exists(dummy_share_path):
    open(dummy_share_path, 'a').close()
    print(f"Created dummy file: {dummy_share_path}")
if not os.path.exists(dummy_pe_eps_path):
    open(dummy_pe_eps_path, 'a').close()
    print(f"Created dummy file: {dummy_pe_eps_path}")

try:
    print("Starting PDF generation test with Chinese characters...")
    result = ReportLabUtils.build_annual_report(
        ticker_symbol='TEST', 
        save_path='test_chinese_report.pdf',
        operating_results="公司2023年营收表现强劲，利润大幅增长。",
        market_position="公司在全球市场占据重要地位，尤其在亚洲市场增长迅速。",
        business_overview="这是一家领先的科技公司，专注于搜索引擎、云计算和在线广告。",
        risk_assessment="市场竞争激烈，需要关注新的监管政策。",
        competitors_analysis="主要竞争对手包括行业内的其他巨头。",
        share_performance_image_path=dummy_share_path,
        pe_eps_performance_image_path=dummy_pe_eps_path,
        filing_date='2024-01-30'
    )
    print(f"Report generation result: {result}")
    if os.path.exists('test_chinese_report.pdf'):
        print("PDF 'test_chinese_report.pdf' was successfully generated.")
        # To verify content, we would ideally extract text or visually inspect.
        # For this automated test, we rely on the absence of errors and file creation.
        # Check file size to ensure it's not empty (basic check)
        file_size = os.path.getsize('test_chinese_report.pdf')
        print(f"Generated PDF size: {file_size} bytes.")
        if file_size == 0:
            print("Warning: Generated PDF is empty.")
            
    else:
        print("Error: PDF 'test_chinese_report.pdf' was not found after generation attempt.")

except Exception as e:
    print(f"An error occurred during PDF generation: {e}")
    print(traceback.format_exc())

finally:
    # Clean up dummy files
    print("Cleaning up dummy files...")
    if os.path.exists(dummy_share_path):
        os.remove(dummy_share_path)
        print(f"Removed {dummy_share_path}")
    if os.path.exists(dummy_pe_eps_path):
        os.remove(dummy_pe_eps_path)
        print(f"Removed {dummy_pe_eps_path}")
    print("Cleanup complete.")

