import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Blockchain } from './blockchain';



@Component({
  selector: 'app-root',
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  // Props:
  public blockchain = inject(Blockchain);
  public username: string = '';
  public privateKeyInput: string = '';
  public recipientAddress: string = '';
  public amountToSend: number = 0.0;
  public ismining = false;

  public ngOnInit(): void {
    this.blockchain.refreshChain(); //інформація про останнні транзакції
    const savedKey = localStorage.getItem('crypto_key')
    if (savedKey) {
      this.onLogin(savedKey);
    }
  }

  public onRegister() {
    this.blockchain.register(this.username).subscribe((res: any) => {
      this.handleAuth(res);
    })
  }

  public onLogin(key?: string) {
    const pk = key || this.privateKeyInput;
    this.blockchain.login(pk).subscribe({
      next: (res: any) => this.handleAuth(res),
      error: () => alert('Ключ не вірний!')
    })
  }


  public handleAuth(user: any) {
    this.blockchain.user.set(user);
    localStorage.setItem('crypto_key', user.privateKey);
  }


  public onLogout() {
    this.blockchain.user.set(null);
    localStorage.removeItem('crypto_key');
  }


  public onMine() {
    this.ismining = true;
    this.blockchain.mine(this.blockchain.user().address).subscribe(() => {
      this.blockchain.refreshChain();
      this.onLogin(this.blockchain.user().private_key);
      this.ismining = false;
    }
    )
  }



  public onSend() {
    this.blockchain
      .sendTransaction(this.recipientAddress, this.amountToSend)
      .subscribe(() => {
        alert('Транзакція відправлена!');
        this.onLogin(this.blockchain.user().privateKey);
      }
      )
  }
}