using System.Net;
using System.Security.Cryptography;

namespace AutoTimetable
{
    /// <summary>
    /// The Timetable class handles downloading a PDF file, calculating its hash, and saving it to disk.
    /// </summary>
    public class Timetable
    {
        private string _pdfUrl; // Stores the URL of the PDF file.
        private MemoryStream? pdfStream; // Memory stream to hold the downloaded PDF data.
        private string? hash; // Cached hash value of the PDF file.
        private readonly HttpClient _httpClient; // HttpClient dependency for downloading the PDF file.

        /// <summary>
        /// Gets the file name from the URL by splitting the URL string.
        /// </summary>
        private string FileName
        {
            get
            {
                return this._pdfUrl.Split("/").Last();
            }
        }

        /// <summary>
        /// Public property to get the hash of the PDF. If the hash is not yet calculated, it triggers the calculation.
        /// </summary>
        public string? Hash
        {
            get
            {
                if (this.hash == null)
                {
                    this.hash = HashFromPDF().Result;
                }
                return this.hash;
            }
        }

        /// <summary>
        /// Constructor that initializes the Timetable object with a PDF URL.
        /// </summary>
        /// <param name="pdfUrl">The URL of the PDF file to be downloaded.</param>
        public Timetable(string pdfUrl, HttpClient? httpClient = null)
        {
            this._pdfUrl = pdfUrl;
            this._httpClient = httpClient ?? new HttpClient();
        }

        /// <summary>
        /// Private method to download the PDF file from the specified URL.
        /// </summary>
        /// <returns>Returns true if the download is successful; otherwise, false.</returns>
        private async Task<bool> downloadPDF()
        {
            try
            {
                using (var response = await this._httpClient.GetAsync(this._pdfUrl))
                {
                    using (var stream = await response.Content.ReadAsStreamAsync())
                    {
                        this.pdfStream = new MemoryStream();
                        await stream.CopyToAsync(pdfStream);
                    }
                }
            }
            catch
            {
                this.pdfStream = null;
                return false;
            }
            return true;
        }

        /// <summary>
        /// Calculates and returns the MD5 hash of the downloaded PDF file.
        /// </summary>
        /// <returns>A string representing the hash in hexadecimal format, or null if the PDF could not be downloaded.</returns>
        public async Task<string?> HashFromPDF()
        {
            if (this.pdfStream == null)
            {
                bool downloadSuccess = await downloadPDF();
                if (!downloadSuccess)
                {
                    return null;
                }
                else if (this.pdfStream != null)
                {
                    this.pdfStream.Position = 0;

                    using (var md5 = MD5.Create())
                    {
                        byte[] hash = md5.ComputeHash(this.pdfStream);
                        return BitConverter.ToString(hash).Replace("-", "").ToLowerInvariant();
                    }
                }
            }
            return null;
        }

        /// <summary>
        /// Saves the downloaded PDF file to the specified directory.
        /// </summary>
        /// <param name="path">The directory path where the PDF should be saved.</param>
        /// <returns>Returns true if the file is saved successfully; otherwise, false.</returns>
        public async Task<bool> SaveToFile(string path)
        {
            if (this.pdfStream == null)
            {
                bool downloadSuccess = await downloadPDF();
                if (!downloadSuccess)
                {
                    return false;
                }
            }
            try
            {
                using (FileStream file = new FileStream(path + this.FileName, FileMode.Create, FileAccess.Write))
                {
                    this.pdfStream?.WriteTo(file);
                }
            }
            catch
            {
                return false;
            }
            return true;
        }
    }
}
