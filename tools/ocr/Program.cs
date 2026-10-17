using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Windows.Globalization;
using Windows.Graphics.Imaging;
using Windows.Media.Ocr;
using Windows.Storage;

// usage: ocr <dir> <out.tsv> [scale]
class P
{
    static async Task Main(string[] a)
    {
        var eng = OcrEngine.TryCreateFromLanguage(new Language("ja"));
        int scale = a.Length > 2 ? int.Parse(a[2]) : 2;
        var sb = new StringBuilder();
        var files = Directory.GetFiles(a[0], "*.png").OrderBy(x => x).ToArray();
        int n = 0;
        foreach (var f in files)
        {
            try
            {
                var file = await StorageFile.GetFileFromPathAsync(Path.GetFullPath(f));
                using var st = await file.OpenAsync(FileAccessMode.Read);
                var dec = await BitmapDecoder.CreateAsync(st);
                uint w = dec.PixelWidth * (uint)scale, h = dec.PixelHeight * (uint)scale;
                if (w > OcrEngine.MaxImageDimension || h > OcrEngine.MaxImageDimension) { w = dec.PixelWidth; h = dec.PixelHeight; }
                var tr = new BitmapTransform { ScaledWidth = w, ScaledHeight = h, InterpolationMode = BitmapInterpolationMode.Linear };
                var bmp = await dec.GetSoftwareBitmapAsync(BitmapPixelFormat.Bgra8, BitmapAlphaMode.Premultiplied, tr, ExifOrientationMode.IgnoreExifOrientation, ColorManagementMode.DoNotColorManage);
                var res = await eng.RecognizeAsync(bmp);
                var lines = string.Join(" | ", res.Lines.Select(l => {
                    double x0 = l.Words.Min(x => x.BoundingRect.X) / scale, y0 = l.Words.Min(x => x.BoundingRect.Y) / scale;
                    double x1 = l.Words.Max(x => x.BoundingRect.X + x.BoundingRect.Width) / scale, y1 = l.Words.Max(x => x.BoundingRect.Y + x.BoundingRect.Height) / scale;
                    return string.Concat(l.Words.Select(x => x.Text)) + string.Format(" @{0:0},{1:0},{2:0},{3:0}", x0, y0, x1 - x0, y1 - y0);
                }));
                sb.Append(Path.GetFileName(f)).Append('\t').Append(lines.Replace('\t', ' ')).Append('\n');
            }
            catch (Exception e) { sb.Append(Path.GetFileName(f)).Append("\tERR ").Append(e.Message).Append('\n'); }
            if (++n % 200 == 0) Console.WriteLine(n);
        }
        File.WriteAllText(a[1], sb.ToString(), new UTF8Encoding(false));
    }
}
