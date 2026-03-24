import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import logging

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ---- CLASS 1: DataLoader ----
class DataLoader:
    def __init__(self, filepath):
        self.filepath = filepath
        self.df = None

    def load(self):
        try:
            self.df = pd.read_csv(self.filepath)
            self.df = self.df.dropna(subset=['title', 'vote_average', 'revenue', 'budget'])
            self.df = self.df.drop_duplicates()
            self.df = self.df[self.df['budget'] > 0]
            self.df = self.df[self.df['revenue'] > 0]
            self.df = self.df.reset_index(drop=True)
            self.df['profit'] = self.df['revenue'] - self.df['budget']
            logging.info(f"Data loaded: {len(self.df)} rows")
            print("✅ Data loaded and cleaned.")
            return self.df
        except FileNotFoundError:
            logging.error("CSV file not found.")
            print("❌ Error: CSV file not found.")
            exit()
        except Exception as e:
            logging.error(f"Data loading failed: {e}")
            print(f"❌ Error: {e}")
            exit()


# ---- CLASS 2: Analyzer ----
class Analyzer:
    def __init__(self, df):
        self.df = df
        self.stats = {}

    def analyze(self):
        try:
            self.stats['avg_budget'] = self.df['budget'].mean()
            self.stats['avg_revenue'] = self.df['revenue'].mean()
            self.stats['avg_rating'] = self.df['vote_average'].mean()
            self.stats['best_movie'] = self.df.loc[self.df['vote_average'].idxmax(), 'title']
            self.stats['most_profitable'] = self.df.loc[self.df['profit'].idxmax(), 'title']
            self.stats['max_profit'] = self.df['profit'].max()
            self.stats['total'] = len(self.df)
            logging.info("Analysis complete.")
            print("✅ Analysis complete.")
            return self.stats
        except Exception as e:
            logging.error(f"Analysis failed: {e}")
            print(f"❌ Analysis error: {e}")
            exit()

    def generate_charts(self):
        try:
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            fig.suptitle('Movie Data Analysis', fontsize=16, fontweight='bold')

            top_revenue = self.df.nlargest(10, 'revenue')
            axes[0, 0].barh(top_revenue['title'], top_revenue['revenue'] / 1e9, color='steelblue')
            axes[0, 0].set_title('Top 10 Movies by Revenue')
            axes[0, 0].set_xlabel('Revenue (Billions $)')

            axes[0, 1].hist(self.df['vote_average'], bins=20, color='coral', edgecolor='black')
            axes[0, 1].set_title('Movie Rating Distribution')
            axes[0, 1].set_xlabel('Rating')

            axes[1, 0].scatter(self.df['budget'] / 1e6, self.df['revenue'] / 1e6, alpha=0.4, color='green')
            axes[1, 0].set_title('Budget vs Revenue')
            axes[1, 0].set_xlabel('Budget (Millions $)')
            axes[1, 0].set_ylabel('Revenue (Millions $)')

            top_profit = self.df.nlargest(10, 'profit')
            axes[1, 1].barh(top_profit['title'], top_profit['profit'] / 1e9, color='purple')
            axes[1, 1].set_title('Top 10 Most Profitable Movies')
            axes[1, 1].set_xlabel('Profit (Billions $)')

            plt.tight_layout()
            plt.savefig('charts.png', dpi=150)
            plt.close()
            logging.info("Charts saved.")
            print("✅ Charts generated.")
        except Exception as e:
            logging.error(f"Chart error: {e}")
            print(f"❌ Chart error: {e}")
            exit()


# ---- CLASS 3: ReportGenerator ----
class ReportGenerator:
    def __init__(self, stats):
        self.stats = stats

    def generate(self):
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 20)
            pdf.cell(0, 15, 'Movie Data Analysis Report', ln=True, align='C')
            pdf.ln(5)
            pdf.set_draw_color(100, 100, 100)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(8)
            pdf.set_font('Arial', 'B', 13)
            pdf.cell(0, 10, 'Key Statistics', ln=True)
            pdf.set_font('Arial', '', 11)
            pdf.cell(0, 8, f"Total Movies Analyzed: {self.stats['total']}", ln=True)
            pdf.cell(0, 8, f"Average Budget:  ${self.stats['avg_budget']:,.0f}", ln=True)
            pdf.cell(0, 8, f"Average Revenue: ${self.stats['avg_revenue']:,.0f}", ln=True)
            pdf.cell(0, 8, f"Average Rating:  {self.stats['avg_rating']:.2f} / 10", ln=True)
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 13)
            pdf.cell(0, 10, 'Highlights', ln=True)
            pdf.set_font('Arial', '', 11)
            pdf.cell(0, 8, f"Highest Rated Movie:   {self.stats['best_movie']}", ln=True)
            pdf.cell(0, 8, f"Most Profitable Movie: {self.stats['most_profitable']}", ln=True)
            pdf.cell(0, 8, f"Maximum Profit:        ${self.stats['max_profit']:,.0f}", ln=True)
            pdf.ln(8)
            pdf.set_font('Arial', 'B', 13)
            pdf.cell(0, 10, 'Visual Analysis', ln=True)
            pdf.image('charts.png', x=10, w=190)
            pdf.output('report.pdf')
            logging.info("PDF created.")
            print("✅ PDF report created.")
        except Exception as e:
            logging.error(f"PDF error: {e}")
            print(f"❌ PDF error: {e}")
            exit()


# ---- CLASS 4: EmailSender ----
class EmailSender:
    def __init__(self, sender, password, receiver):
        self.sender = sender
        self.password = password
        self.receiver = receiver

    def send(self, filepath):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = self.receiver
            msg['Subject'] = 'Movie Data Analysis Report'
            msg.attach(MIMEText('Hi,\n\nPlease find the automated analysis report attached.\n\nRegards', 'plain'))

            with open(filepath, 'rb') as f:
                attachment = MIMEBase('application', 'octet-stream')
                attachment.set_payload(f.read())
                encoders.encode_base64(attachment)
                attachment.add_header('Content-Disposition', f'attachment; filename={filepath}')
                msg.attach(attachment)

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.sender, self.password)
                server.sendmail(self.sender, self.receiver, msg.as_string())

            logging.info("Email sent.")
            print("✅ Email sent successfully!")
        except smtplib.SMTPAuthenticationError:
            logging.error("Email auth failed.")
            print("❌ Wrong Gmail or app password.")
        except Exception as e:
            logging.error(f"Email error: {e}")
            print(f"❌ Email error: {e}")


# ---- MAIN: Run Everything ----
if __name__ == '__main__':
    loader = DataLoader('tmdb_5000_movies.csv')
    df = loader.load()

    analyzer = Analyzer(df)
    stats = analyzer.analyze()
    analyzer.generate_charts()

    report = ReportGenerator(stats)
    report.generate()

    emailer = EmailSender(
        sender='samonaslam102@gmail.com',
        password='epid ulea kjxp jodj',
        receiver='adanaslam99@gmail.com'
    )
    emailer.send('report.pdf')