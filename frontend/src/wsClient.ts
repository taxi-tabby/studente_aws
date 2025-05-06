import * as WebSocket from 'ws';

export class WebSocketClient {
  private socket: WebSocket | null = null;
  private readonly url: string;
  private reconnectInterval: number = 2000;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private onMessageCallback: (message: any) => void;
  private isConnecting: boolean = false;

  constructor(port: number = 20200, onMessage: (message: any) => void) {
    this.url = `ws://127.0.0.1:${port}`;
    this.onMessageCallback = onMessage;
  }

  public connect(): void {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      console.log('WebSocket already connected or connecting');
      return;
    }

    if (this.isConnecting) {
      return;
    }

    this.isConnecting = true;

    try {
      this.socket = new WebSocket(this.url);

      this.socket.on('open', () => {
        console.log('WebSocket connection established');
        this.isConnecting = false;
        
        // Clear any reconnection timeout if it exists
        if (this.reconnectTimeout) {
          clearTimeout(this.reconnectTimeout);
          this.reconnectTimeout = null;
        }
      });

      this.socket.on('message', (data: WebSocket.Data) => {
        try {
          let message: string;
          
          if (data instanceof Buffer) {
            message = data.toString('utf8');
          } else if (typeof data === 'string') {
            message = data;
          } else {
            // Handle other types of data if needed
            message = String(data);
          }

          console.log(`WebSocket message received: ${message}`);
          
          let parsedData;
          try {
            parsedData = JSON.parse(message);
          } catch (e) {
            // If not valid JSON, pass as string
            parsedData = message;
          }
          
          this.onMessageCallback(parsedData);
        } catch (error) {
          console.error('Error processing WebSocket message:', error);
        }
      });

      this.socket.on('close', () => {
        console.log('WebSocket connection closed');
        this.isConnecting = false;
        this.scheduleReconnect();
      });

      this.socket.on('error', (err) => {
        console.error(`WebSocket error: ${err.message}`);
        this.isConnecting = false;
        this.socket?.close();
        this.scheduleReconnect();
      });

    } catch (error) {
      console.error('Failed to connect to WebSocket server:', error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (!this.reconnectTimeout) {
      console.log(`Scheduling WebSocket reconnect in ${this.reconnectInterval}ms`);
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

    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  public send(message: string | object): boolean {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('Cannot send message: WebSocket is not connected');
      this.connect(); // Try to reconnect
      return false;
    }

    try {
      const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
      this.socket.send(messageStr);
      return true;
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
      return false;
    }
  }

  public isConnected(): boolean {
    return !!this.socket && this.socket.readyState === WebSocket.OPEN;
  }
}