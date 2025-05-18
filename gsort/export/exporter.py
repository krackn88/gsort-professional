"""
Export module for gSort Professional.
Provides functionality to export combos and analytics in various formats.
"""

import os
import json
import csv
import logging
from typing import List, Dict, Any, Optional, BinaryIO
from datetime import datetime
import pandas as pd
from matplotlib.figure import Figure

from gsort.analytics.analyzer import AnalyticsResult


class ComboExporter:
    """
    Export combos and analytics in various formats.
    """
    
    def __init__(self):
        """Initialize the exporter"""
        self.logger = logging.getLogger(__name__)
    
    def export_text(self, combos: List[str], file_path: str) -> bool:
        """
        Export combos to a plain text file.
        
        Args:
            combos: List of email:password combinations
            file_path: Path where the file will be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for combo in combos:
                    f.write(f"{combo}\n")
            
            self.logger.info(f"Exported {len(combos)} combos to {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting to text file: {e}")
            return False
    
    def export_csv(self, combos: List[str], file_path: str) -> bool:
        """
        Export combos to a CSV file with email and password columns.
        
        Args:
            combos: List of email:password combinations
            file_path: Path where the file will be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create DataFrame with email and password columns
            df = pd.DataFrame(combos, columns=['combo'])
            df[['email', 'password']] = df['combo'].str.split(':', n=1, expand=True)
            
            # Drop the combo column
            df = df[['email', 'password']]
            
            # Export to CSV
            df.to_csv(file_path, index=False)
            
            self.logger.info(f"Exported {len(combos)} combos to CSV: {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}")
            return False
    
    def export_excel(self, combos: List[str], file_path: str) -> bool:
        """
        Export combos to an Excel file with email and password columns and basic formatting.
        
        Args:
            combos: List of email:password combinations
            file_path: Path where the file will be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create DataFrame with email and password columns
            df = pd.DataFrame(combos, columns=['combo'])
            df[['email', 'password']] = df['combo'].str.split(':', n=1, expand=True)
            
            # Drop the combo column
            df = df[['email', 'password']]
            
            # Create a writer with formatting
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Combos', index=False)
                
                # Get the worksheet
                worksheet = writer.sheets['Combos']
                
                # Format headers
                for cell in worksheet[1]:
                    cell.style = 'Headline 2'
                
                # Adjust column widths
                worksheet.column_dimensions['A'].width = 40
                worksheet.column_dimensions['B'].width = 30
            
            self.logger.info(f"Exported {len(combos)} combos to Excel: {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting to Excel: {e}")
            return False
    
    def export_json(self, combos: List[str], file_path: str) -> bool:
        """
        Export combos to a JSON file.
        
        Args:
            combos: List of email:password combinations
            file_path: Path where the file will be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse combos into a list of dictionaries
            combo_dicts = []
            for combo in combos:
                parts = combo.split(':', 1)
                if len(parts) == 2:
                    email, password = parts
                    combo_dicts.append({
                        'email': email,
                        'password': password
                    })
                else:
                    combo_dicts.append({
                        'combo': combo
                    })
            
            # Export to JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'combos': combo_dicts,
                    'meta': {
                        'count': len(combo_dicts),
                        'exported_at': datetime.now().isoformat(),
                        'generated_by': 'gSort Professional'
                    }
                }, f, indent=2)
            
            self.logger.info(f"Exported {len(combos)} combos to JSON: {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {e}")
            return False
    
    def export_analytics_report(self, 
                               analysis_results: Dict[str, AnalyticsResult], 
                               file_path: str,
                               include_figures: bool = True) -> bool:
        """
        Export analytics results to a comprehensive report.
        
        Args:
            analysis_results: Dictionary of analysis results
            file_path: Path where the file will be saved
            include_figures: Whether to include figures in the report
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine export format based on file extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            if ext == '.json':
                return self._export_analytics_json(analysis_results, file_path)
            elif ext in ('.xlsx', '.xls'):
                return self._export_analytics_excel(analysis_results, file_path)
            elif ext == '.html':
                return self._export_analytics_html(analysis_results, file_path, include_figures)
            elif ext == '.pdf':
                return self._export_analytics_pdf(analysis_results, file_path, include_figures)
            else:
                self.logger.error(f"Unsupported report format: {ext}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error exporting analytics report: {e}")
            return False
    
    def _export_analytics_json(self, analysis_results: Dict[str, AnalyticsResult], file_path: str) -> bool:
        """Export analytics results to JSON format"""
        try:
            # Convert results to dict without figures
            result_dict = {}
            for name, result in analysis_results.items():
                result_dict[name] = {
                    'title': result.title,
                    'description': result.description,
                    'data': result.data,
                    'summary': result.summary
                }
            
            # Add metadata
            export_data = {
                'analytics': result_dict,
                'meta': {
                    'generated_at': datetime.now().isoformat(),
                    'generated_by': 'gSort Professional'
                }
            }
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Exported analytics report to JSON: {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting analytics to JSON: {e}")
            return False
    
    def _export_analytics_excel(self, analysis_results: Dict[str, AnalyticsResult], file_path: str) -> bool:
        """Export analytics results to Excel format"""
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Create a summary sheet
                summary_data = []
                for name, result in analysis_results.items():
                    summary_data.append({
                        'Analysis': result.title,
                        'Description': result.description,
                        'Summary': result.summary
                    })
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Adjust column widths
                worksheet = writer.sheets['Summary']
                worksheet.column_dimensions['A'].width = 30
                worksheet.column_dimensions['B'].width = 40
                worksheet.column_dimensions['C'].width = 60
                
                # Create sheets for each analysis with data tables
                for name, result in analysis_results.items():
                    sheet_name = name[:31]  # Excel limits sheet names to 31 chars
                    
                    # Convert nested data to flat tables where possible
                    data_tables = {}
                    
                    for key, value in result.data.items():
                        if isinstance(value, dict):
                            # Try to convert to DataFrame
                            try:
                                # Handle different dict structures
                                if all(isinstance(v, (int, float)) for v in value.values()):
                                    # Simple key-value dict
                                    df = pd.DataFrame({
                                        'key': list(value.keys()),
                                        'value': list(value.values())
                                    })
                                else:
                                    # Nested dict
                                    df = pd.DataFrame.from_dict(value, orient='index')
                                
                                data_tables[key] = df
                            except:
                                # If conversion fails, skip
                                pass
                        elif isinstance(value, list) and value and isinstance(value[0], dict):
                            # List of dicts
                            try:
                                df = pd.DataFrame(value)
                                data_tables[key] = df
                            except:
                                pass
                    
                    # Write tables to sheet
                    row_position = 0
                    for table_name, df in data_tables.items():
                        # Write table header
                        worksheet = writer.sheets.get(sheet_name)
                        if worksheet is None:
                            # Create new worksheet
                            df.to_excel(writer, sheet_name=sheet_name, startrow=row_position)
                            worksheet = writer.sheets[sheet_name]
                        else:
                            # Write to existing worksheet
                            df.to_excel(writer, sheet_name=sheet_name, startrow=row_position)
                        
                        # Add table name as header
                        worksheet.cell(row=row_position+1, column=1, value=table_name)
                        
                        # Move position for next table
                        row_position += len(df) + 3
            
            self.logger.info(f"Exported analytics report to Excel: {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting analytics to Excel: {e}")
            return False
    
    def _export_analytics_html(self, 
                              analysis_results: Dict[str, AnalyticsResult], 
                              file_path: str,
                              include_figures: bool = True) -> bool:
        """Export analytics results to HTML format"""
        try:
            from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
            import base64
            from io import BytesIO
            
            # HTML head with styles
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>gSort Professional - Analytics Report</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f5f5f5;
                        color: #333;
                    }
                    
                    h1 {
                        color: #2c3e50;
                        border-bottom: 2px solid #3498db;
                        padding-bottom: 10px;
                    }
                    
                    h2 {
                        color: #2980b9;
                        margin-top: 30px;
                    }
                    
                    .section {
                        background-color: white;
                        border-radius: 5px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                        padding: 20px;
                        margin-bottom: 30px;
                    }
                    
                    .description {
                        color: #7f8c8d;
                        font-style: italic;
                        margin-bottom: 20px;
                    }
                    
                    .summary {
                        background-color: #f9f9f9;
                        border-left: 4px solid #2980b9;
                        padding: 15px;
                        margin: 20px 0;
                        white-space: pre-line;
                    }
                    
                    .figure {
                        text-align: center;
                        margin: 20px 0;
                    }
                    
                    .figure img {
                        max-width: 100%;
                        height: auto;
                        border: 1px solid #ddd;
                    }
                    
                    .footer {
                        margin-top: 50px;
                        text-align: center;
                        color: #7f8c8d;
                        font-size: 0.9em;
                    }
                </style>
            </head>
            <body>
                <h1>gSort Professional - Analytics Report</h1>
                <div class="description">Generated on """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</div>
            """
            
            # Add each analysis section
            for name, result in analysis_results.items():
                html += f"""
                <div class="section">
                    <h2>{result.title}</h2>
                    <div class="description">{result.description}</div>
                    <div class="summary">{result.summary}</div>
                """
                
                # Add figures if requested
                if include_figures and result.figures:
                    for i, fig in enumerate(result.figures):
                        # Convert figure to base64 encoded image
                        canvas = FigureCanvas(fig)
                        img_buffer = BytesIO()
                        canvas.print_png(img_buffer)
                        img_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                        
                        html += f"""
                        <div class="figure">
                            <img src="data:image/png;base64,{img_data}" alt="Figure {i+1}">
                        </div>
                        """
                
                html += "</div>"
            
            # Add footer and close tags
            html += """
                <div class="footer">
                    <p>Generated by gSort Professional</p>
                </div>
            </body>
            </html>
            """
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            self.logger.info(f"Exported analytics report to HTML: {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting analytics to HTML: {e}")
            return False
    
    def _export_analytics_pdf(self, 
                             analysis_results: Dict[str, AnalyticsResult], 
                             file_path: str,
                             include_figures: bool = True) -> bool:
        """Export analytics results to PDF format"""
        try:
            # First export to HTML
            html_path = file_path + '.tmp.html'
            if not self._export_analytics_html(analysis_results, html_path, include_figures):
                return False
            
            # Convert HTML to PDF
            try:
                # Try with weasyprint first
                import weasyprint
                weasyprint.HTML(html_path).write_pdf(file_path)
            except ImportError:
                # Fall back to pdfkit
                try:
                    import pdfkit
                    pdfkit.from_file(html_path, file_path)
                except ImportError:
                    self.logger.error("Failed to generate PDF: Neither weasyprint nor pdfkit is available")
                    return False
            
            # Clean up temporary HTML file
            try:
                os.remove(html_path)
            except:
                pass
            
            self.logger.info(f"Exported analytics report to PDF: {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting analytics to PDF: {e}")
            return False