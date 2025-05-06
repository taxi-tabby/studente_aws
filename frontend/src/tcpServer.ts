import * as net from 'net';

export class TcpServer {
  private server: net.Server | null = null;
  private clients: net.Socket[] = [];
  private readonly port: number = 20200;
  private readonly address: string = '127.0.0.1';
  private onMessageCallback: (message: any) => void;

  constructor(onMessage: (message: any) => void) {
    this.onMessageCallback = onMessage;
  }

  public start(): boolean {
    try {
      if (this.server) {
        return true; // Already running
      }

      this.server = net.createServer((socket) => {
        console.log(`Client connected: ${socket.remoteAddress}:${socket.remotePort}`);
        this.clients.push(socket);

        // Handle data from clients
        socket.on('data', (data) => {
          try {
            const messageStr = data.toString('utf8');
            console.log(`TCP message received: ${messageStr}`);
            
            let parsedData;
            try {
              parsedData = JSON.parse(messageStr);
            } catch (e) {
              // If not valid JSON, pass as string
              parsedData = messageStr;
            }
            
            this.onMessageCallback(parsedData);
          } catch (error) {
            console.error('Error processing TCP message:', error);
          }
        });

        // Handle client disconnection
        socket.on('end', () => {
          this.clients = this.clients.filter(client => client !== socket);
          console.log('Client disconnected');
        });

        // Handle errors
        socket.on('error', (err) => {
          console.error(`Socket error: ${err.message}`);
          this.clients = this.clients.filter(client => client !== socket);
        });
      });

      this.server.on('error', (err) => {
        console.error(`TCP server error: ${err.message}`);
        this.stop();
      });

      this.server.listen(this.port, this.address, () => {
        console.log(`TCP server listening on ${this.address}:${this.port}`);
      });

      return true;
    } catch (error) {
      console.error('Failed to start TCP server:', error);
      return false;
    }
  }

  public stop(): void {
    if (this.server) {
      this.server.close();
      this.server = null;
    }
    
    // Close all client connections
    this.clients.forEach(client => {
      try {
        client.destroy();
      } catch (e) {
        console.error('Error closing client connection:', e);
      }
    });
    this.clients = [];
  }

  public send(message: string | object, host: string = '127.0.0.1', port: number = 20200): void {
    try {
      const messageBuffer = typeof message === 'string' 
        ? Buffer.from(message) 
        : Buffer.from(JSON.stringify(message));
      
      // Send to all connected clients
      if (this.clients.length > 0) {
        this.clients.forEach(client => {
          client.write(messageBuffer);
        });
      } else {
        // If no clients are connected, create a temporary connection to send the message
        const tempClient = new net.Socket();
        tempClient.connect(port, host, () => {
          tempClient.write(messageBuffer);
          tempClient.end();
        });
        
        tempClient.on('error', (err) => {
          console.error('Error sending TCP message:', err);
          tempClient.destroy();
        });
      }
    } catch (error) {
      console.error('Failed to send TCP message:', error);
    }
  }
}