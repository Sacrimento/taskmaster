#include<stdio.h>
#include<signal.h>
#include<unistd.h>
#include<stdlib.h>

void sig_handler(int sign)
{
  if (sign == SIGINT)
    printf("received SIGINT\n");
  exit(1);
}

int main(void)
{
  if (signal(SIGINT, sig_handler) == SIG_ERR)
  	printf("\ncan't catch SIGINT\n");
  // A long long wait so that we can easily issue a signal to this process
  while(1) 
    sleep(1);
  return 0;
}
