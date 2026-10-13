import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import java.io.File;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.file.Files;
import java.util.HashMap;
import java.util.Map;

/**
 * SiddhamArchiveServer — Lightweight Java HTTP Hosting Utility for the Siddham Epigraphic Portal.
 * Run directly with Java 11+:
 *     java SiddhamArchiveServer.java
 */
public class SiddhamArchiveServer {
    private static final int PORT = 8085;
    private static final Map<String, String> MIME_TYPES = new HashMap<>();

    static {
        MIME_TYPES.put("html", "text/html; charset=utf-8");
        MIME_TYPES.put("css", "text/css; charset=utf-8");
        MIME_TYPES.put("js", "application/javascript; charset=utf-8");
        MIME_TYPES.put("json", "application/json; charset=utf-8");
        MIME_TYPES.put("xml", "application/xml; charset=utf-8");
        MIME_TYPES.put("pdf", "application/pdf");
        MIME_TYPES.put("png", "image/png");
        MIME_TYPES.put("svg", "image/svg+xml");
    }

    public static void main(String[] args) throws IOException {
        File rootDir = new File(System.getProperty("user.dir")).getCanonicalFile();
        HttpServer server = HttpServer.create(new InetSocketAddress(PORT), 0);
        server.createContext("/", new StaticFileHandler(rootDir));
        server.setExecutor(null);
        System.out.println("====================================================================");
        System.out.println("  Siddham Archive Java HTTP Server running at:");
        System.out.println("  http://localhost:" + PORT + "/index.html");
        System.out.println("====================================================================");
        server.start();
    }

    static class StaticFileHandler implements HttpHandler {
        private final File rootDir;

        public StaticFileHandler(File rootDir) {
            this.rootDir = rootDir;
        }

        @Override
        public void handle(HttpExchange exchange) throws IOException {
            String path = exchange.getRequestURI().getPath();
            if (path.equals("/") || path.isEmpty()) {
                path = "/index.html";
            }
            File target = new File(rootDir, path.substring(1)).getCanonicalFile();
            if (!target.getPath().startsWith(rootDir.getPath()) || !target.exists() || target.isDirectory()) {
                byte[] notFound = "404 Not Found".getBytes();
                exchange.sendResponseHeaders(404, notFound.length);
                try (OutputStream os = exchange.getResponseBody()) {
                    os.write(notFound);
                }
                return;
            }

            String ext = "";
            int dot = target.getName().lastIndexOf('.');
            if (dot >= 0) {
                ext = target.getName().substring(dot + 1).toLowerCase();
            }
            String contentType = MIME_TYPES.getOrDefault(ext, "application/octet-stream");
            exchange.getResponseHeaders().set("Content-Type", contentType);
            exchange.getResponseHeaders().set("Access-Control-Allow-Origin", "*");

            byte[] bytes = Files.readAllBytes(target.toPath());
            exchange.sendResponseHeaders(200, bytes.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(bytes);
            }
        }
    }
}
