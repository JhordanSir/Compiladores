ruray factorial(yupay: yupay) kutipay yupay { 
    sichus yupay == 0 {
        kutipay 1
    } mana {
        kutipay yupay * factorial(yupay - 1)
    }
}

ruray hatun_ruray() {
    imprimiy(factorial(5))
}