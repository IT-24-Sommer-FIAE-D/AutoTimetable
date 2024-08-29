using AutoTimetable;
using Moq;
using Moq.Protected;
using System.Net;
using System.Security.Cryptography;
using System.Text;

namespace AutoTimetable.Tests
{
    public class TimetableTests
    {
        [Fact]
        public async Task HashFromPDF_ReturnsCorrectHash_WhenDownloadIsSuccessful()
        {
            // Arrange
            var pdfUrl = "https://example.com/timetable.pdf";
            var pdfContent = Encoding.UTF8.GetBytes("This is a test PDF content.");
            var expectedHash = CalculateMd5Hash(pdfContent);

            var mockHandler = new Mock<HttpMessageHandler>();
            mockHandler
                .Protected()
                .Setup<Task<HttpResponseMessage>>(
                    "SendAsync",
                    ItExpr.IsAny<HttpRequestMessage>(),
                    ItExpr.IsAny<CancellationToken>())
                .ReturnsAsync(new HttpResponseMessage
                {
                    StatusCode = HttpStatusCode.OK,
                    Content = new ByteArrayContent(pdfContent)
                });

            var httpClient = new HttpClient(mockHandler.Object);
            var timetable = new Timetable(pdfUrl, httpClient);

            // Act
            var result = await timetable.HashFromPDF();

            // Assert
            Assert.Equal(expectedHash, result);
        }

        [Fact]
        public async Task HashFromPDF_ReturnsNull_WhenDownloadFails()
        {
            // Arrange
            var pdfUrl = "https://example.com/timetable.pdf";

            var mockHandler = new Mock<HttpMessageHandler>();
            mockHandler
                .Protected()
                .Setup<Task<HttpResponseMessage>>(
                    "SendAsync",
                    ItExpr.IsAny<HttpRequestMessage>(),
                    ItExpr.IsAny<CancellationToken>())
                .ThrowsAsync(new HttpRequestException());

            var httpClient = new HttpClient(mockHandler.Object);

            var timetable = new Timetable(pdfUrl, httpClient);

            // Act
            var result = await timetable.HashFromPDF();

            // Assert
            Assert.Null(result);
        }

        [Fact]
        public async Task SaveToFile_SavesFileSuccessfully_WhenDownloadIsSuccessful()
        {
            // Arrange
            var pdfUrl = "https://example.com/timetable.pdf";
            var pdfContent = Encoding.UTF8.GetBytes("This is a test PDF content.");
            var tempPath = Path.GetTempPath();
            var expectedFilePath = Path.Combine(tempPath, "timetable.pdf");

            var mockHandler = new Mock<HttpMessageHandler>();
            mockHandler
                .Protected()
                .Setup<Task<HttpResponseMessage>>(
                    "SendAsync",
                    ItExpr.IsAny<HttpRequestMessage>(),
                    ItExpr.IsAny<CancellationToken>())
                .ReturnsAsync(new HttpResponseMessage
                {
                    StatusCode = HttpStatusCode.OK,
                    Content = new ByteArrayContent(pdfContent)
                });

            var httpClient = new HttpClient(mockHandler.Object);
            var timetable = new Timetable(pdfUrl, httpClient);

            // Act
            var result = await timetable.SaveToFile(tempPath);

            // Assert
            Assert.True(result);
            Assert.True(File.Exists(expectedFilePath));
            Assert.Equal(pdfContent, File.ReadAllBytes(expectedFilePath));

            // Cleanup
            File.Delete(expectedFilePath);
        }

        [Fact]
        public async Task SaveToFile_ReturnsFalse_WhenDownloadFails()
        {
            // Arrange
            var pdfUrl = "https://example.com/timetable.pdf";
            var tempPath = Path.GetTempPath();

            var mockHandler = new Mock<HttpMessageHandler>();
            mockHandler
                .Protected()
                .Setup<Task<HttpResponseMessage>>(
                    "SendAsync",
                    ItExpr.IsAny<HttpRequestMessage>(),
                    ItExpr.IsAny<CancellationToken>())
                .ThrowsAsync(new HttpRequestException());

            var httpClient = new HttpClient(mockHandler.Object);
            var timetable = new Timetable(pdfUrl, httpClient);

            // Act
            var result = await timetable.SaveToFile(tempPath);

            // Assert
            Assert.False(result);
        }

        private string CalculateMd5Hash(byte[] input)
        {
            using (var md5 = MD5.Create())
            {
                var hash = md5.ComputeHash(input);
                return BitConverter.ToString(hash).Replace("-", "").ToLowerInvariant();
            }
        }
    }
}
