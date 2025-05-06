import * as net from 'net';

export class TcpClient {
  private client: net.Socket | null = null;
  private readonly port: number = 20200; 
  private readonly host: string = '127.0.0.1';
  private onMessageCallback: (message: any) => void;
  private reconnectInterval: number = 3000;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private isConnecting: boolean = false;
  private buffer: string = '';

  constructor(onMessage: (message: any) => void) {
    this.onMessageCallback = onMessage;
  }

  public connect(): boolean {
    if (this.client && !this.client.destroyed) {
      console.log('TCP client already connected');
      return true;
    }

    if (this.isConnecting) {
      return false;
    }

    this.isConnecting = true;

    try {
      this.client = new net.Socket();
      
      this.client.on('connect', () => {
        console.log(`TCP client connected to ${this.host}:${this.port}`);
        this.isConnecting = false;
        
        // Clear any reconnection timeout if it exists
        if (this.reconnectTimeout) {
          clearTimeout(this.reconnectTimeout);
          this.reconnectTimeout = null;
        }
      });

      this.client.on('data', (data: Buffer) => {
        try {
          // Add received data to buffer
          this.buffer += data.toString('utf8');
          
          // Process complete messages
          this.processBuffer();
        } catch (error) {
          console.error('Error processing TCP message:', error);
        }
      });

      this.client.on('close', () => {
        console.log('TCP connection closed');
        this.isConnecting = false;
        this.client = null;
        this.scheduleReconnect();
      });

      this.client.on('error', (err) => {
        console.error(`TCP client error: ${err.message}`);
        this.isConnecting = false;
        this.client?.destroy();
        this.client = null;
        this.scheduleReconnect();
      });

      this.client.connect(this.port, this.host);
      return true;
    } catch (error) {
      console.error('Failed to connect to TCP server:', error);
      this.isConnecting = false;
      this.scheduleReconnect();
      return false;
    }
  }

  private processBuffer(): void {
    // Simple implementation assuming each message ends with a newline
    // This can be improved for more complex protocols
    const messages = this.buffer.split('\n');
    
    // If the last element doesn't end with '\n', it's incomplete
    if (messages.length > 0 && this.buffer.endsWith('\n')) {
      this.buffer = ''; // All messages were complete, clear buffer
    } else if (messages.length > 0) {
      this.buffer = messages.pop() || ''; // Keep the incomplete message in buffer
    }

    messages.forEach(msg => {
      if (msg.trim() === '') return;
      
      console.log(`TCP message received: ${msg}`);
      
      let parsedData;
      try {
        parsedData = JSON.parse(msg);
      } catch (e) {
        // If not valid JSON, pass as string
        parsedData = msg;
      }
      
      this.onMessageCallback(parsedData);
    });
  }

  private scheduleReconnect(): void {
    if (!this.reconnectTimeout) {
      console.log(`Scheduling TCP reconnect in ${this.reconnectInterval}ms`);
      this.reconnectTimeout = setTimeout(() => {
        this.reconnectTimeout = null;
        this.connect();
      }, this.reconnectInterval);
    }
  }

  public disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.client && !this.client.destroyed) {
      this.client.destroy();
      this.client = null;
    }
  }

  public send(message: string | object): boolean {
    if (!this.client || this.client.destroyed) {
      console.error('Cannot send message: TCP client is not connected');
      this.connect(); // Try to reconnect
      return false;
    }

    try {
      const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
      this.client.write(messageStr + '\n'); // Adding newline as message delimiter
      return true;
    } catch (error) {
      console.error('Failed to send TCP message:', error);
      return false;
    }
  }

  public isConnected(): boolean {
    return !!this.client && !this.client.destroyed;
  }
}