export interface UserResponse {
	user_id: number;
	email: string;
	name: string;
}

export interface TokenWithUserResponse {
	access_token: string;
	token_type: string;
	user: UserResponse;
}


