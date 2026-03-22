import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ec as EC } from 'elliptic';

import { routes } from './app.routes';
import { provideHttpClient } from '@angular/common/http';

const ec = new EC('secp256k1');

@Injectable({
  providedIn: 'root',
})
export class Blockchain {
  // ->
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8000';

  public user = signal<any>(null);
  public chain = signal<any[]>([]);


  public register(username: string) {
    return this.http.post(`${this.apiUrl}/register?username=${username}`, {})
  }

  //   $.ajax
  //   ({
  //       url: '....',
  //       data: `username=${}&price=${}`,
  //       success: ()=> {

  //       }
  // })

  public login(privateKey: string) {
    return this.http.post(`${this.apiUrl}/login?privateKey=${privateKey}`, {})
  }


  public refreshChain() {
    this.http
      .get<any[]>(`${this.apiUrl}/chain`)
      .subscribe((res) => this.chain.set(res));
  }



  public mine(address: string) {
    return this.http.post(`${this.apiUrl}/mine?miner_address=${address}`, {})
  }

  public get_user_contacts() {
    const privateKey = this.user().privateKey;
    return this.http.get(`${this.apiUrl}/contacts?private_key=${privateKey}`);
  }


  public addContact(nickname: string, contact_address: string) {
    const payload = {
      owner_address: this.user().address,
      future_contact_address: contact_address,
      nickname: nickname
    };
    return this.http.post(`${this.apiUrl}/add_contact`, payload);
  }

  public sendTransaction(recipient: string, amount: number) {
    const privateKey = this.user().privateKey;
    const key = ec.keyFromPrivate(privateKey);

    const message = recipient + amount;
    const signature = key.sign(message).toDER('hex');

    const payload = {
      sender_address: this.user().address,
      recipient_address: recipient,
      amount: amount,
      signature: signature,
    }

    return this.http.post(`${this.apiUrl}/send`, payload);
  }
}
