use std::{io::{Read, Write}, net::TcpStream};

fn main() -> std::io::Result<()> {
    let mut stream = TcpStream::connect("192.168.4.1:8080")?;
    let mut buf = vec![0;1024];
    loop {
        let l = stream.read(&mut buf)?;
        if l > 0 {
            println!("{}",l);
        }
        stream.write_all(&mut buf[..l])?;
    }
}